"""市场交易统计 — DailyInfoCollector."""
import logging
import time
from datetime import datetime, timedelta

from src.collectors.base import BaseTushareCollector
from src.models.daily_info import RawDailyInfo
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class DailyInfoCollector(BaseTushareCollector):
    """市场交易统计 (daily_info API)."""

    model = RawDailyInfo
    api_name = "daily_info"
    checkpoint_key = "daily_info"

    def __init__(self, token: str):
        super().__init__("daily_info", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        return self.api_call(self.api_name, trade_date=trade_date, limit=4000)

    def validate(self, raw: list[dict]) -> list[dict]:
        import math
        validated = []
        _i = lambda v: int(v) if (v is not None and not (isinstance(v, float) and math.isnan(v))) else None
        for x in raw:
            validated.append({
                "trade_date": str(x.get("trade_date", "")),
                "ts_code": str(x.get("ts_code", "")),
                "ts_name": str(x.get("ts_name", "")),
                "com_count": _i(x.get("com_count")),
                "total_share": _f(x.get("total_share")),
                "float_share": _f(x.get("float_share")),
                "total_mv": _f(x.get("total_mv")),
                "float_mv": _f(x.get("float_mv")),
                "amount": _f(x.get("amount")),
                "vol": _f(x.get("vol")),
                "trans_count": _i(x.get("trans_count")),
                "pe": _f(x.get("pe")),
                "tr": _f(x.get("tr")),
                "exchange": str(x.get("exchange", "")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawDailyInfo, records, ["trade_date", "ts_code"])

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
            time.sleep(0.21)

        logger.info(f"daily_info DONE: {days} days, {total:,} rows, {errors} err, {int(time.time()-t0)}s")
        return {"status": "success", "written": total, "days": days, "errors": errors, "elapsed": time.time() - t0}
