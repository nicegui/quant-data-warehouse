"""美股交易日历 — UsTradeCalCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.us_market import RefUsTradeCal
from src.collectors.base import BaseTushareCollector

class UsTradeCalCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("us_tradecal", token)
    def fetch(self, **kw): return self.api_call("us_tradecal")
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:x.get(k)for k in("cal_date","is_open","pretrade_date")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RefUsTradeCal).filter_by(cal_date=r["cal_date"]).first()
                if not e:s.add(RefUsTradeCal(**r));w+=1
        return w
