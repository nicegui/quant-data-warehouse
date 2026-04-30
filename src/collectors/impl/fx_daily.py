"""外汇日线 — FxDailyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.fx_market import RawFxDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class FxDailyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("fx_daily", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        return self.api_call("fx_daily",**p)
    def validate(self, raw):
        r=[]
        nf=("bid_open","bid_close","bid_high","bid_low","ask_open","ask_close","ask_high","ask_low","tick_qty")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","trade_date","bid_open","bid_close","bid_high","bid_low","ask_open","ask_close","ask_high","ask_low","tick_qty")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawFxDaily).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawFxDaily(**r));w+=1
        return w
