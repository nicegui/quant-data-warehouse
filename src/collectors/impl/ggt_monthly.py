"""港股通月度成交 — GgtMonthlyCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.moneyflow import RawGgtMonthly
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class GgtMonthlyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("ggt_monthly", token)
    @property
    def checkpoint_key(self): return "month"
    def fetch(self, month="", **kw):
        p={}
        if month:p["month"]=month
        return self.api_call("ggt_monthly",**p)
    def validate(self, raw):
        r=[]
        nf=("day_buy_amt","day_buy_vol","day_sell_amt","day_sell_vol","total_buy_amt","total_buy_vol","total_sell_amt","total_sell_vol")
        for x in raw: r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("month","day_buy_amt","day_buy_vol","day_sell_amt","day_sell_vol","total_buy_amt","total_buy_vol","total_sell_amt","total_sell_vol")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawGgtMonthly, records, ["month"])
