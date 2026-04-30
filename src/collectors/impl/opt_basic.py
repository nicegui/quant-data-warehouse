"""期权基本信息 — OptBasicCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.opt_market import RefOptBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class OptBasicCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("opt_basic", token)
    def fetch(self, exchange="", **kw):
        p={}
        if exchange:p["exchange"]=exchange
        return self.api_call("opt_basic",**p)
    def validate(self, raw):
        r=[]
        nf=("exercise_price","list_price")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","exchange","name","per_unit","opt_code","opt_type","call_put","exercise_type","exercise_price","s_month","maturity_date","list_price","list_date","delist_date","last_edate","last_ddate","quote_unit","min_price_chg")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RefOptBasic).filter_by(ts_code=r["ts_code"]).first()
                if not e:s.add(RefOptBasic(**r));w+=1
        return w
