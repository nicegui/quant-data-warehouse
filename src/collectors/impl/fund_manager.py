"""基金经理 — FundManagerCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.fund import RawFundManager
from src.collectors.base import BaseTushareCollector

class FundManagerCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("fund_manager", token)
    @property
    def checkpoint_key(self): return "ann_date"
    def fetch(self, ts_code="", ann_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if ann_date:p["ann_date"]=ann_date
        return self.api_call("fund_manager",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("ts_code","ann_date","name","gender","birth_year","edu","nationality","begin_date","end_date","resume")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFundManager, records, ["ts_code", "name"])
