"""Abstract base class for all data collectors."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.session import db_session
from src.models.pipeline import PipelineLog


class BaseCollector(ABC):
    """Abstract collector with common retry, logging, and audit infrastructure."""

    def __init__(self, name: str):
        self.name = name
        self._max_retries = 3
        self._retry_delay = 5  # seconds

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

    def run(self, **kwargs) -> dict:
        """Full run: fetch → validate → store_raw → audit.

        Returns a dict with run summary.
        """
        started_at = datetime.now(timezone.utc)
        config_snapshot = {"collector": self.name, "params": kwargs}

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
                }

            # Step 2: Validate
            validated = self.validate(raw_data)

            # Step 3: Store raw
            written = self.store_raw(validated)

            # Step 4: Audit
            self._log_pipeline(started_at, "success", records_fetched, written, config_snapshot)

            return {
                "status": "success",
                "fetched": records_fetched,
                "written": written,
            }

        except Exception as e:
            self._log_pipeline(started_at, "failed", 0, 0, config_snapshot, str(e))
            return {
                "status": "failed",
                "fetched": 0,
                "written": 0,
                "error": str(e),
            }

    def compute_curated(self, **kwargs) -> int:
        """Compute curated layer from raw layer (override for specific pipelines)."""
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
