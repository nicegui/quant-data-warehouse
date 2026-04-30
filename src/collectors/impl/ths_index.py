"""同花顺板块指数 — ThsIndexCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.index import RefThsIndex
from src.collectors.base import BaseTushareCollector

class ThsIndexCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("ths_index", token)
    def fetch(self, exchange="", **kw):
        p={}
        if exchange:p["exchange"]=exchange
        return self.api_call("ths_index",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("ts_code","name","count","exchange","list_date","type")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RefThsIndex).filter_by(ts_code=r["ts_code"]).first()
                if not e:s.add(RefThsIndex(**r));w+=1
        return w
