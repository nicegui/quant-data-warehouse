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
        import math
        r=[]
        for x in raw:
            cnt = x.get("count")
            if cnt is None or (isinstance(cnt, float) and math.isnan(cnt)):
                cnt = None
            ld = x.get("list_date")
            if ld is None or (isinstance(ld, float) and math.isnan(ld)):
                ld = None
            r.append({"ts_code": x.get("ts_code"), "name": x.get("name"),
                      "count": int(cnt) if cnt is not None else None,
                      "exchange": x.get("exchange"),
                      "list_date": str(ld) if ld else None,
                      "type": x.get("type")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RefThsIndex).filter_by(ts_code=r["ts_code"]).first()
                if not e:s.add(RefThsIndex(**r));w+=1
        return w
