"""管理层薪酬 — StkRewardsCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.fundamental import RawStkRewards
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class StkRewardsCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("stk_rewards", token)
    @property
    def checkpoint_key(self): return "end_date"
    def fetch(self, ts_code="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        else: p["ts_code"]="000001.SZ"
        if end_date:p["end_date"]=end_date
        return self.api_call("stk_rewards",**p)
    def validate(self, raw):
        r=[]
        for x in raw: r.append({k:_f(x.get(k))if k in("reward","hold_vol")else x.get(k)for k in("ts_code","ann_date","end_date","name","title","reward","hold_vol")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawStkRewards).filter_by(ts_code=r["ts_code"],ann_date=r["ann_date"],name=r["name"]).first()
                if not e:s.add(RawStkRewards(**r));w+=1
        return w
