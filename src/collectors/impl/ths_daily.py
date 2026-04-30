"""同花顺板块日线 — ThsDailyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.index import RawThsDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class ThsDailyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("ths_daily", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        return self.api_call("ths_daily",**p)
    def validate(self, raw):
        r=[]
        nf=("open","high","low","close","pre_close","avg_price","change","pct_change","vol","turnover_rate")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","trade_date","open","high","low","close","pre_close","avg_price","change","pct_change","vol","turnover_rate")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawThsDaily).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawThsDaily(**r));w+=1
        return w
