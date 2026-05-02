"""DC Concept (东方财富概念题材) collector."""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from src.collectors.base import BaseTushareCollector
from src.models.dc_concept import RawDcConcept

logger = logging.getLogger(__name__)


class DcConceptCollector(BaseTushareCollector):
    """Collect东方财富概念题材 daily list (data from 20260203)."""

    model = RawDcConcept
    api_name = "dc_concept"
    checkpoint_key = "dc_concept"

    def __init__(self, token: str):
        super().__init__("dc_concept", token)

    def fetch(self, trade_date: Optional[str] = None, **kwargs) -> list[dict]:
        params = {"limit": 5000}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call(self.api_name, **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        _s = lambda v: str(v) if v is not None else None
        validated = []
        for row in raw:
            validated.append({
                "theme_code": str(row.get("theme_code", "")),
                "trade_date": str(row.get("trade_date", "")),
                "name": str(row.get("name", "")),
                "pct_change": _s(row.get("pct_change")),
                "hot": _s(row.get("hot")),
                "sort": _s(row.get("sort")),
                "strength": _s(row.get("strength")),
                "z_t_num": _s(row.get("z_t_num")),
                "main_change": _s(row.get("main_change")),
                "lead_stock": _s(row.get("lead_stock")),
                "lead_stock_code": _s(row.get("lead_stock_code")),
                "lead_stock_pct_change": _s(row.get("lead_stock_pct_change")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Not called; inline in run()."""
        return len(records)

    def run(self, start_date: str = "20260203", end_date: Optional[str] = None) -> dict:
        """迭代日期从 20260203 到今，按天采集."""
        from src.db.session import db_session
        from sqlalchemy import text

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
                raw = self.fetch(trade_date=d_str)
                if raw:
                    validated = self.validate(raw)
                    with db_session() as session:
                        # Dedup by (theme_code, trade_date)
                        for rec in validated:
                            existing = session.query(RawDcConcept).filter_by(
                                theme_code=rec["theme_code"],
                                trade_date=rec["trade_date"],
                            ).first()
                            if not existing:
                                session.add(RawDcConcept(**rec))
                                total_written += 1
                            else:
                                for k, v in rec.items():
                                    if k != "id":
                                        setattr(existing, k, v)
                                total_written += 1
                        session.commit()
                    days_processed += 1
                else:
                    days_processed += 1  # empty day still counts
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
            f"dc_concept DONE: {days_processed} days, "
            f"{total_written:,} rows, {errors} errors, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "written": total_written,
            "days": days_processed,
            "errors": errors,
            "elapsed": elapsed,
        }
