"""中信行业指数日线 — CiDailyCollector."""
import logging
import time
from datetime import datetime, timedelta

from src.collectors.base import BaseTushareCollector
from src.models.ci_daily import RawCiDaily
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class CiDailyCollector(BaseTushareCollector):
    """中信行业指数日线 (ci_daily API)."""

    model = RawCiDaily
    api_name = "ci_daily"
    checkpoint_key = "ci_daily"

    def __init__(self, token: str):
        super().__init__("ci_daily", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        return self.api_call(self.api_name, trade_date=trade_date, limit=4000)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        nf = ("open","low","high","close","pre_close","change","pct_change","vol","amount")
        for x in raw:
            validated.append({
                k: _f(x.get(k)) if k in nf else str(x.get(k, ""))
                for k in ("ts_code","trade_date","open","low","high","close","pre_close","change","pct_change","vol","amount")
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawCiDaily, records, ["ts_code", "trade_date"])


    def run(self) -> dict:
        t0 = time.time()
        total, errors, days = 0, 0, 0
        d = datetime(2020,1,1)
        end = datetime(2026,5,3)

        while d <= end:
            try:
                date_str = d.strftime("%Y%m%d")
                raw = self.fetch(trade_date=date_str)
                if raw:
                    total += self.store_raw(self.validate(raw))
                days += 1
            except Exception as e:
                logger.error(f"[{d.strftime('%Y%m%d')}] ERROR: {e}")
                errors += 1
            d += timedelta(days=1)

            if days % 200 == 0:
                logger.info(f"[{date_str}] {days} days, {total:,} rows | {days/(time.time()-t0):.1f} d/s")
            time.sleep(0.21)

        elapsed = time.time() - t0
        logger.info(f"ci_daily DONE: {days} days, {total:,} rows, {errors} err, {int(elapsed)}s")
        return {"status":"success","written":total,"days":days,"errors":errors,"elapsed":elapsed}
