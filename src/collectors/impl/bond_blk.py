"""债券大宗交易 — BondBlkCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.bond import RawBondBlk
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class BondBlkCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("bond_blk", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, trade_date="", ts_code="", **kw):
        p={}
        if trade_date:p["trade_date"]=trade_date
        if ts_code:p["ts_code"]=ts_code
        return self.api_call("bond_blk",**p)
    def validate(self, raw):
        r=[]
        for x in raw:
            r.append({"trade_date":x.get("trade_date"),"ts_code":x.get("ts_code",""),"name":x.get("name"),"price":_f(x.get("price")),"vol":_f(x.get("vol")),"amount":_f(x.get("amount"))})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawBondBlk).filter_by(trade_date=r["trade_date"],ts_code=r["ts_code"]).first()
                if not e:s.add(RawBondBlk(**r));w+=1
        return w
