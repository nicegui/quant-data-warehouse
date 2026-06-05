"""大盘指数每日指标 — IndexDailyBasicCollector"""
from __future__ import annotations
from typing import Any
from src.db.session import db_session
from src.models.market import RawIndexDailyBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class IndexDailyBasicCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("index_dailybasic", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw) -> list[dict]:
        p = {}
        if ts_code: p["ts_code"] = ts_code
        if trade_date: p["trade_date"] = trade_date
        if start_date: p["start_date"] = start_date
        if end_date: p["end_date"] = end_date
        if not p:
            from datetime import date, timedelta
            p["trade_date"] = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        return self.api_call("index_dailybasic", **p)

    def validate(self, raw):
        result = []
        fields = ("ts_code","trade_date","total_mv","float_mv","total_share","float_share","free_share","turnover_rate","turnover_rate_f","pe","pe_ttm","pb")
        for r in raw:
            result.append({k: _f(r.get(k)) if k.startswith(("total","float","free","turn","pe","pb")) else r.get(k) for k in fields})
        return result

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawIndexDailyBasic, records, ["ts_code", "trade_date"])

    def run(self) -> dict:
        import time, logging
        logger = logging.getLogger(__name__)
        t0 = time.time(); total = 0
        codes = ["000001.SH","399001.SZ","000016.SH","000905.SH","399005.SZ","399006.SZ"]
        for ts_code in codes:
            raw = self.fetch(ts_code=ts_code, start_date="20040101", end_date="20260502")
            if raw:
                n = self.store_raw(self.validate(raw))
                total += n
                logger.info(f"[{ts_code}] {n} rows")
            time.sleep(0.21)
        logger.info(f"index_dailybasic DONE: {total} rows, {int(time.time()-t0)}s")
        return {"status":"success","written":total,"elapsed":time.time()-t0}
