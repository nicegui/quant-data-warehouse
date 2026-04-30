"""上市公司管理层 — StkManagersCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.fundamental import RawStkManagers
from src.collectors.base import BaseTushareCollector

class StkManagersCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("stk_managers", token)
    @property
    def checkpoint_key(self): return "ann_date"
    def fetch(self, ts_code="", ann_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if ann_date:p["ann_date"]=ann_date
        return self.api_call("stk_managers",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("ts_code","ann_date","name","gender","lev","title","edu","national","birthday","begin_date","end_date")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawStkManagers).filter_by(ts_code=r["ts_code"],name=r["name"],title=r.get("title")).first()
                if not e:s.add(RawStkManagers(**r));w+=1
        return w
