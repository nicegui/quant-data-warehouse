"""指数月线 — IndexMonthlyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.market import RawIndexMonthly
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class IndexMonthlyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("index_monthly", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        return self.api_call("index_monthly",**p)
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
                e=s.query(RawIndexMonthly).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawIndexMonthly(**r));w+=1
        return w
