"""涨跌停列表全量 — LimitListAllCollector"""
from __future__ import annotations
from typing import Any
from src.db.session import db_session
from src.models.market import RawLimitListAll
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class LimitListAllCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("limit_list", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, trade_date="", ts_code="", start_date="", end_date="", **kw):
        p = {}
        if trade_date: p["trade_date"] = trade_date
        if ts_code: p["ts_code"] = ts_code
        return self.api_call("limit_list", **p)
    def validate(self, raw):
        r = []
        nf = ("close","pct_chg","amp","fc_ratio","fl_ratio","fd_amount","strth")
        for x in raw:
            r.append({k: _f(x.get(k)) if k in nf else x.get(k) for k in ("trade_date","ts_code","name","close","pct_chg","amp","fc_ratio","fl_ratio","fd_amount","first_time","last_time","open_times","strth","limit")})
        return r
    def store_raw(self, recs):
        w=0
        with db_session() as s:
            for r in recs:
                e=s.query(RawLimitListAll).filter_by(trade_date=r["trade_date"],ts_code=r["ts_code"]).first()
                if not e: s.add(RawLimitListAll(**r)); w+=1
        return w
