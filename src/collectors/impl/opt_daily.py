"""期权日线 — OptDailyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.opt_market import RawOptDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class OptDailyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("opt_daily", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        return self.api_call("opt_daily",**p)
    def validate(self, raw):
        r=[]
        nf=("pre_settle","pre_close","open","high","low","close","settle","vol","amount","oi")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","trade_date","exchange","pre_settle","pre_close","open","high","low","close","settle","vol","amount","oi")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawOptDaily).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawOptDaily(**r));w+=1
        return w
