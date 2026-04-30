"""港股分钟行情 — HkMinsCollector
⚠️ 频次限制: 2次/小时
"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.hk_market import RawHkMins
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class HkMinsCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("hk_mins", token)
    @property
    def checkpoint_key(self): return "trade_time"
    def fetch(self, ts_code="", freq="1min", **kw):
        return self.api_call("hk_mins",ts_code=ts_code,freq=freq)
    def validate(self, raw):
        r=[]
        nf=("open","close","high","low","vol","amount")
        for x in raw: r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","trade_time","open","close","high","low","vol","amount")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawHkMins).filter_by(ts_code=r["ts_code"],trade_time=r["trade_time"]).first()
                if not e:s.add(RawHkMins(**r));w+=1
        return w
