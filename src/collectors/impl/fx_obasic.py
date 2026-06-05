"""外汇基础信息 — FxBasicCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.fx_market import RefFxBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class FxBasicCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("fx_obasic", token)
    def fetch(self, exchange="", **kw):
        p={}
        if exchange:p["exchange"]=exchange
        return self.api_call("fx_obasic",**p)
    def validate(self, raw):
        r=[]
        nf=("min_unit","max_unit","pip","pip_cost","traget_spread","min_stop_distance")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","name","classify","exchange","min_unit","max_unit","pip","pip_cost","traget_spread","min_stop_distance","trading_hours","break_time")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefFxBasic, records, ["ts_code"])
