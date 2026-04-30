"""财经日历 — EcoCalCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.events import RawEcoCal
from src.collectors.base import BaseTushareCollector

class EcoCalCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("eco_cal", token)
    @property
    def checkpoint_key(self): return "date"
    def fetch(self, date="", **kw):
        p={}
        if date:p["date"]=date
        return self.api_call("eco_cal",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("date","time","currency","country","event","value","pre_value","fore_value")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawEcoCal).filter_by(date=r["date"],event=r.get("event")).first()
                if not e:s.add(RawEcoCal(**r));w+=1
        return w
