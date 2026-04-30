"""指数周线 — IndexWeeklyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.market import RawIndexWeekly
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class IndexWeeklyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("index_weekly", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        if start_date:p["start_date"]=start_date
        if end_date:p["end_date"]=end_date
        if not p:
            from datetime import date, timedelta
            p["trade_date"]=(date.today()-timedelta(days=1)).strftime("%Y%m%d")
        return self.api_call("index_weekly",**p)
    def validate(self, raw):
        r=[]
        ohcl=("close","open","high","low","pre_close","change","pct_chg","vol","amount")
        for x in raw:
            r.append({k:_f(x.get(k))if k in ohcl else x.get(k)for k in("ts_code","trade_date","close","open","high","low","pre_close","change","pct_chg","vol","amount")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawIndexWeekly).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawIndexWeekly(**r));w+=1
        return w
