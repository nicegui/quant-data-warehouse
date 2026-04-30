"""LPR利率 — ShiborLprCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.rate import RawShiborLpr
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class ShiborLprCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("shibor_lpr", token)
    @property
    def checkpoint_key(self): return "date"
    def fetch(self, date="", **kw):
        p={}
        if date:p["date"]=date
        return self.api_call("shibor_lpr",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({"date":x.get("date"),"y1":_f(x.get("1y")),"y5":_f(x.get("5y"))})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawShiborLpr).filter_by(date=r["date"]).first()
                if not e:s.add(RawShiborLpr(**r));w+=1
        return w
