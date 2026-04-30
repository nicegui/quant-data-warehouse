"""港股列表 — HkBasicCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.hk_market import RefHkBasic
from src.collectors.base import BaseTushareCollector

class HkBasicCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("hk_basic", token)
    def fetch(self, **kw): return self.api_call("hk_basic")
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("ts_code","name","fullname","enname","cn_spell","market","list_status","list_date","delist_date","trade_unit","isin","curr_type")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RefHkBasic).filter_by(ts_code=r["ts_code"]).first()
                if not e:s.add(RefHkBasic(**r));w+=1
        return w
