"""沪深港通成分股 — HsConstCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.moneyflow import RefHsConst
from src.collectors.base import BaseTushareCollector

class HsConstCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("hs_const", token)
    def fetch(self, hs_type="SH", **kw):
        return self.api_call("hs_const",hs_type=hs_type)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("ts_code","hs_type","in_date","out_date","is_new")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefHsConst, records, ["ts_code", "hs_type"])
