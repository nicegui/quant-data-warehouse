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
        return self.api_call("index_dailybasic", **p)

    def validate(self, raw):
        result = []
        fields = ("ts_code","trade_date","total_mv","float_mv","total_share","float_share","free_share","turnover_rate","turnover_rate_f","pe","pe_ttm","pb")
        for r in raw:
            result.append({k: _f(r.get(k)) if k.startswith(("total","float","free","turn","pe","pb")) else r.get(k) for k in fields})
        return result

    def store_raw(self, recs):
        w = 0
        with db_session() as s:
            for r in recs:
                e = s.query(RawIndexDailyBasic).filter_by(ts_code=r["ts_code"], trade_date=r["trade_date"]).first()
                if not e: s.add(RawIndexDailyBasic(**r)); w += 1
        return w
