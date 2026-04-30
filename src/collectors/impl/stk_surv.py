"""机构调研 — StkSurvCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.news import RawStkSurv
from src.collectors.base import BaseTushareCollector

class StkSurvCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("stk_surv", token)
    @property
    def checkpoint_key(self): return "surv_date"
    def fetch(self, ts_code="", surv_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if surv_date:p["surv_date"]=surv_date
        return self.api_call("stk_surv",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("ts_code","name","surv_date","fund_visitors","rece_place","rece_mode","rece_org","org_type","comp_rece")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawStkSurv).filter_by(ts_code=r["ts_code"],surv_date=r["surv_date"],rece_org=r.get("rece_org","")).first()
                if not e:s.add(RawStkSurv(**r));w+=1
        return w
