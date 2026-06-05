"""DC Concept Cons (东方财富题材成分股) collector."""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from src.collectors.base import BaseTushareCollector
from src.models.dc_concept_cons import RawDcConceptCons

logger = logging.getLogger(__name__)


class DcConceptConsCollector(BaseTushareCollector):
    """Collect东方财富题材成分股 (data from 20260203)."""

    model = RawDcConceptCons
    api_name = "dc_concept_cons"
    checkpoint_key = "dc_concept_cons"

    def __init__(self, token: str):
        super().__init__("dc_concept_cons", token)

    def fetch(self, trade_date: str) -> Optional[list]:
        return self.api_call(self.api_name, trade_date=trade_date, limit=8000)

    def validate(self, raw: list[dict]) -> list[dict]:
        _s = lambda v: str(v) if v is not None else None
        validated = []
        for row in raw:
            validated.append({
                "ts_code": str(row.get("ts_code", "")),
                "trade_date": str(row.get("trade_date", "")),
                "name": str(row.get("name", "")),
                "theme_code": str(row.get("theme_code", "")),
                "industry_code": _s(row.get("industry_code")),
                "industry": _s(row.get("industry")),
                "reason": _s(row.get("reason")),
                "hot_num": _s(row.get("hot_num")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Not called; inline in run()."""
        return len(records)

    def run(self, start_date: str = "20260203", end_date: Optional[str] = None) -> dict:
        from src.db.session import db_session

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        last_date = self.get_checkpoint_date()
        if last_date:
            last_date = last_date.replace("-", "")
            start = datetime.strptime(last_date, "%Y%m%d") + timedelta(days=1)
            start_date = start.strftime("%Y%m%d")
            logger.info(f"Resuming from checkpoint date: {start_date}")

        d = datetime.strptime(start_date, "%Y%m%d")
        end_d = datetime.strptime(end_date, "%Y%m%d")

        total_written = 0
        errors = 0
        days_processed = 0
        t0 = time.time()

        while d <= end_d:
            d_str = d.strftime("%Y%m%d")

            try:
                raw = self.fetch(d_str)
                if raw:
                    validated = self.validate(raw)
                    written = self._store_dedup(RawDcConceptCons, validated, ["ts_code", "theme_code", "trade_date"])
                    total_written += written
                days_processed += 1
            except Exception as e:
                logger.error(f"[{d_str}] ERROR: {e}")
                errors += 1

            d += timedelta(days=1)
            time.sleep(0.21)

            if days_processed % 50 == 0:
                elapsed = time.time() - t0
                d_per_s = days_processed / elapsed if elapsed > 0 else 0
                days_left = (end_d - d).days + 1
                eta = int(days_left / d_per_s) if d_per_s > 0 else None
                logger.info(
                    f"[{d_str}] {days_processed} days, {total_written:,} rows | "
                    f"{d_per_s:.2f} d/s"
                    + (f" ETA {eta}s" if eta else "")
                )

            if days_processed % 100 == 0:
                self._update_checkpoint(d_str, total_written)

        self._update_checkpoint(end_date, total_written)
        elapsed = time.time() - t0
        logger.info(
            f"dc_concept_cons DONE: {days_processed} days, "
            f"{total_written:,} rows, {errors} errors, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "written": total_written,
            "days": days_processed,
            "errors": errors,
            "elapsed": elapsed,
        }
