"""指数技术因子(专业版) — IdxFactorProCollector."""
import json
import logging
import time
from datetime import datetime, timedelta

from src.collectors.base import BaseTushareCollector
from src.models.idx_factor_pro import RawIdxFactorPro

logger = logging.getLogger(__name__)


class IdxFactorProCollector(BaseTushareCollector):
    """指数技术因子 (idx_factor_pro API)."""

    model = RawIdxFactorPro
    api_name = "idx_factor_pro"
    checkpoint_key = "idx_factor_pro"

    def __init__(self, token: str):
        super().__init__("idx_factor_pro", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        return self.api_call(self.api_name, trade_date=trade_date, limit=8000)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": str(row.get("ts_code", "")),
                "trade_date": str(row.get("trade_date", "")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawIdxFactorPro, records, ["ts_code", "trade_date"])

    def run(self) -> dict:
        t0 = time.time()
        total, errors, days = 0, 0, 0
        d = datetime(2020, 1, 1)
        end = datetime(2026, 5, 3)

        while d <= end:
            date_str = d.strftime("%Y%m%d")
            try:
                raw = self.fetch(trade_date=date_str)
                if raw:
                    total += self.store_raw(self.validate(raw))
                days += 1
            except Exception as e:
                logger.error(f"[{date_str}] ERROR: {e}")
                errors += 1

            d += timedelta(days=1)

            if days % 200 == 0:
                logger.info(f"[{date_str}] {days} days, {total:,} rows | {days/(time.time()-t0):.1f} d/s")
            time.sleep(0.61)  # 30 calls/min rate limit

        elapsed = time.time() - t0
        logger.info(f"idx_factor_pro DONE: {days} days, {total:,} rows, {errors} err, {int(elapsed)}s")
        return {"status": "success", "written": total, "days": days, "errors": errors, "elapsed": elapsed}
