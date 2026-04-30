"""券商月度荐股 — BrokerRecommendCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.events import RefBrokerRecommend
from src.collectors.base import BaseTushareCollector

class BrokerRecommendCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("broker_recommend", token)
    @property
    def checkpoint_key(self): return "month"
    def fetch(self, month="", **kw):
        p={}
        if month:p["month"]=month
        return self.api_call("broker_recommend",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("month","broker","ts_code","name")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RefBrokerRecommend).filter_by(month=r["month"],broker=r.get("broker"),ts_code=r.get("ts_code")).first()
                if not e:s.add(RefBrokerRecommend(**r));w+=1
        return w
