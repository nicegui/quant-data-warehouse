"""Shibor报价 — ShiborQuoteCollector"""
from __future__ import annotations; from typing import Any
from src.db.session import db_session
from src.models.rate import RawShiborQuote
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class ShiborQuoteCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("shibor_quote", token)
    @property
    def checkpoint_key(self): return "date"
    def fetch(self, date="", **kw):
        p={}
        if date:p["date"]=date
        return self.api_call("shibor_quote",**p)
    def validate(self, raw):
        r=[]
        nf=("on_b","on_a","1w_b","1w_a","2w_b","2w_a","1m_b","1m_a","3m_b","3m_a","6m_b","6m_a","9m_b","9m_a","1y_b","1y_a")
        for x in raw: r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("date","bank","on_b","on_a","1w_b","1w_a","2w_b","2w_a","1m_b","1m_a","3m_b","3m_a","6m_b","6m_a","9m_b","9m_a","1y_b","1y_a")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawShiborQuote, records, ["date"])
