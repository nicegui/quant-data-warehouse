"""Hibor利率 — HiborCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.rate import RawHibor
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class HiborCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("hibor", token)
    @property
    def checkpoint_key(self): return "date"
    def fetch(self, date="", **kw):
        p={}
        if date:p["date"]=date
        return self.api_call("hibor",**p)
    def validate(self, raw):
        r=[]
        nf=("on","1w","2w","1m","2m","3m","6m","12m")
        for x in raw: r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("date","on","1w","2w","1m","2m","3m","6m","12m")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawHibor, records, ["date"])
