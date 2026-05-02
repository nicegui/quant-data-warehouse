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

    def run(self) -> dict:
        import time, logging
        logger = logging.getLogger(__name__)
        t0 = time.time(); total = 0
        codes = ["XIN9","HSI","HKTECH","HKAH","DJI","SPX","IXIC","FTSE","FCHI",
                 "GDAXI","N225","KS11","AS51","SENSEX","IBOVESPA","RTS",
                 "TWII","CKLSE","SPTSX","CSX5P","RUT"]
        for ts_code in codes:
            raw = self.fetch(ts_code=ts_code)
            if raw:
                total += self.store_raw(self.validate(raw))
                logger.info(f"[{ts_code}] {len(raw)} rows")
            time.sleep(0.21)
        logger.info(f"index_global DONE: {total} rows, {int(time.time()-t0)}s")
        return {"status":"success","written":total,"elapsed":time.time()-t0}
