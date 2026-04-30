"""全球指数 — IndexGlobalCollector"""
from __future__ import annotations
from typing import Any
from src.db.session import db_session
from src.models.market import RawIndexGlobal
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class IndexGlobalCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("index_global", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw) -> list[dict]:
        p = {}
        if ts_code: p["ts_code"] = ts_code
        if trade_date: p["trade_date"] = trade_date
        return self.api_call("index_global", **p)

    def validate(self, raw):
        result = []
        ohcl = ("open","close","high","low","pre_close","change","pct_chg","swing","vol")
        for r in raw:
            result.append({k: _f(r.get(k)) if k in ohcl else r.get(k) for k in ("ts_code","trade_date","open","close","high","low","pre_close","change","pct_chg","swing","vol")})
        return result

    def store_raw(self, recs):
        w = 0
        with db_session() as s:
            for r in recs:
                e = s.query(RawIndexGlobal).filter_by(ts_code=r["ts_code"], trade_date=r["trade_date"]).first()
                if not e: s.add(RawIndexGlobal(**r)); w += 1
        return w
