"""Abstract base class for all data collectors — with checkpoint/resume support."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.session import db_session
from src.models.pipeline import PipelineLog
from src.utils.checkpoint import CheckpointManager


class BaseCollector(ABC):
    """Abstract collector with retry, logging, audit, and checkpoint/resume.

    Subclasses can override:
      - checkpoint_key: return the date field name to enable checkpointing
      - fetch_resumable: pull only data after the checkpoint date
    """

    def __init__(self, name: str):
        self.name = name
        self._max_retries = 3
        self._retry_delay = 5  # seconds
        self._checkpoint_manager: CheckpointManager | None = None
        self._enable_checkpoint = True

    # ── Abstract interface ──

    @abstractmethod
    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch raw data from the source API."""
        ...

    @abstractmethod
    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate and transform raw data into canonical form."""
        ...

    @abstractmethod
    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records into raw layer tables."""
        ...

    # ── Checkpoint support ──

    @property
    def checkpoint(self) -> CheckpointManager:
        """Lazy checkpoint manager for this collector."""
        if self._checkpoint_manager is None:
            self._checkpoint_manager = CheckpointManager(self.name)
        return self._checkpoint_manager

    @property
    def checkpoint_key(self) -> Optional[str]:
        """Override to enable checkpointing.

        Return the date field name that tracks progress, e.g.:
          - "trade_date" for daily collectors (stock_daily, index_daily, moneyflow...)
          - "ann_date" for dividend/announcement collectors
          - "end_date" for range-based collectors
          - None to disable checkpointing (e.g. stock_basic, concept — always full pull)
        """
        return None

    def get_checkpoint_date(self) -> Optional[str]:
        """Get the last successful date from checkpoint."""
        key = self.checkpoint_key
        if key is None:
            return None
        return self.checkpoint.get(key)

    def _update_checkpoint(self, date_val: str, written: int) -> None:
        """Save checkpoint after a successful run."""
        key = self.checkpoint_key
        if key is None:
            return
        state = self.checkpoint.load()
        prev_written = state.get("total_written", 0)
        prev_errors = state.get("total_errors", 0)
        self.checkpoint.save(
            **{key: date_val},
            total_written=prev_written + written,
            total_errors=prev_errors,
            last_run_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── Main pipeline ──

    def run(self, **kwargs) -> dict:
        """Full run: fetch → validate → store_raw → audit.

        If checkpoint_key is set, automatically resumes from last saved date
        and saves checkpoint on success.

        Returns a dict with run summary.
        """
        started_at = datetime.now(timezone.utc)
        config_snapshot = {"collector": self.name, "params": kwargs}

        # ── Resume: inject checkpoint date if not explicitly provided ──
        ck_key = self.checkpoint_key
        if ck_key and ck_key not in kwargs:
            last_date = self.get_checkpoint_date()
            if last_date:
                kwargs[ck_key] = last_date

        try:
            # Step 1: Fetch
            raw_data = self._fetch_with_retry(**kwargs)
            records_fetched = len(raw_data)

            if records_fetched == 0:
                self._log_pipeline(started_at, "success", 0, 0, config_snapshot)
                return {
                    "status": "success",
                    "fetched": 0,
                    "written": 0,
                    "message": "No new data",
                    "checkpoint": self.get_checkpoint_date(),
                }

            # Step 2: Validate
            validated = self.validate(raw_data)

            # Step 3: Store raw (each collector dedupes internally)
            written = self.store_raw(validated)

            # Step 4: Save checkpoint
            if ck_key and written > 0:
                # Extract the max date from validated records
                latest_date = self._extract_max_date(validated, ck_key)
                if latest_date:
                    self._update_checkpoint(latest_date, written)

            # Step 5: Audit
            self._log_pipeline(started_at, "success", records_fetched, written, config_snapshot)

            return {
                "status": "success",
                "fetched": records_fetched,
                "written": written,
                "checkpoint": self.get_checkpoint_date(),
            }

        except Exception as e:
            self._log_pipeline(started_at, "failed", 0, 0, config_snapshot, str(e))
            return {
                "status": "failed",
                "fetched": 0,
                "written": 0,
                "error": str(e),
                "checkpoint": self.get_checkpoint_date(),
            }

    def compute_curated(self, **kwargs) -> int:
        """Compute curated layer from raw (override for specific pipelines)."""
        return 0

    # ── Internal helpers ──

    def _fetch_with_retry(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch with exponential backoff retry."""
        last_error = None
        for attempt in range(self._max_retries):
            try:
                return self.fetch(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    time.sleep(delay)
        raise last_error  # type: ignore[misc]

    def _extract_max_date(self, records: list[dict], key: str) -> Optional[str]:
        """Find the latest date value across all records."""
        max_val: Optional[str] = None
        for rec in records:
            val = rec.get(key)
            if val is not None:
                val_str = str(val)[:10]  # normalize: "2025-01-15" or "20250115" -> first 10 chars
                if max_val is None or val_str > max_val:
                    max_val = val_str
        return max_val

    def _log_pipeline(
        self,
        started_at: datetime,
        status: str,
        fetched: int,
        written: int,
        config: dict,
        error: Optional[str] = None,
    ):
        """Write pipeline audit log."""
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        record = PipelineLog(
            pipeline_name=self.name,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            records_fetched=fetched,
            records_written=written,
            error_message=error,
            config_snapshot=str(config),
        )
        try:
            with db_session() as session:
                session.add(record)
        except Exception:
            pass  # Don't let audit failure break the pipeline


class BaseTushareCollector(BaseCollector):
    """Base collector for Tushare Pro API sources."""

    def __init__(self, name: str, token: str):
        super().__init__(name)
        self.token = token
        self._pro = None

    @property
    def pro(self):
        """Lazy Tushare API instance."""
        if self._pro is None:
            import tushare as ts
            self._pro = ts.pro_api(self.token)
        return self._pro

    def api_call(self, api_name: str, **params) -> list[dict]:
        """Make a Tushare API call with basic error handling."""
        api = getattr(self.pro, api_name)
        df = api(**params)
        if df is None or df.empty:
            return []
        return df.to_dict(orient="records")
