"""盘前集合竞价 — StkAuctionCollector"""
from __future__ import annotations
from typing import Any
from src.db.session import db_session
from src.models.market import RawStkAuction
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class StkAuctionCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("stk_auction", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw) -> list[dict]:
        p = {}
        if ts_code: p["ts_code"] = ts_code
        if trade_date: p["trade_date"] = trade_date
        if start_date: p["start_date"] = start_date
        if end_date: p["end_date"] = end_date
        return self.api_call("stk_auction", **p)

    def validate(self, raw):
        result = []
        for r in raw:
            result.append({k: r.get(k) for k in ("ts_code","trade_date","vol","price","amount","pre_close","turnover_rate","volume_ratio","float_share")})
        return result

    def store_raw(self, recs):
        w = 0
        with db_session() as s:
            for r in recs:
                e = s.query(RawStkAuction).filter_by(ts_code=r["ts_code"], trade_date=r["trade_date"]).first()
                if not e:
                    s.add(RawStkAuction(**r)); w += 1
        return w
