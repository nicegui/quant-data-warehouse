"""温州民间借贷利率 — WzIndexCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.rate import RawWzIndex
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class WzIndexCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("wz_index", token)
    @property
    def checkpoint_key(self): return "date"
    def fetch(self, date="", **kw):
        p={}
        if date:p["date"]=date
        return self.api_call("wz_index",**p)
    def validate(self, raw):
        r=[]
        nf=("comp_rate","center_rate","micro_rate","cm_rate","sdb_rate","om_rate","aa_rate","m1_rate","m3_rate","m6_rate","m12_rate","long_rate")
        for x in raw: r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("date","comp_rate","center_rate","micro_rate","cm_rate","sdb_rate","om_rate","aa_rate","m1_rate","m3_rate","m6_rate","m12_rate","long_rate")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawWzIndex).filter_by(date=r["date"]).first()
                if not e:s.add(RawWzIndex(**r));w+=1
        return w
