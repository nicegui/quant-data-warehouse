"""Libor利率 — LiborCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.rate import RawLibor
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class LiborCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("libor", token)
    @property
    def checkpoint_key(self): return "date"
    def fetch(self, date="", **kw):
        p={}
        if date:p["date"]=date
        return self.api_call("libor",**p)
    def validate(self, raw):
        r=[]
        nf=("on","1w","1m","2m","3m","6m","12m")
        for x in raw: r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("date","curr_type","on","1w","1m","2m","3m","6m","12m")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawLibor).filter_by(date=r["date"],curr_type=r.get("curr_type")).first()
                if not e:s.add(RawLibor(**r));w+=1
        return w
