"""期权基本信息 — OptBasicCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.opt_market import RefOptBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class OptBasicCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("opt_basic", token)
    def fetch(self, exchange="", **kw):
        p={}
        if exchange:p["exchange"]=exchange
        return self.api_call("opt_basic",**p)
    def validate(self, raw):
        r=[]
        nf=("exercise_price","list_price")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","exchange","name","per_unit","opt_code","opt_type","call_put","exercise_type","exercise_price","s_month","maturity_date","list_price","list_date","delist_date","last_edate","last_ddate","quote_unit","min_price_chg")})
        return r
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefOptBasic, records, ["ts_code"])

    def run(self) -> dict:
        import time, logging
        logger = logging.getLogger(__name__)
        t0 = time.time(); total = 0
        for ex in ("SSE","SZSE","DCE","CFFEX"):
            raw = self.fetch(exchange=ex)
            if raw:
                n = self.store_raw(self.validate(raw))
                total += n
                logger.info(f"[{ex}] {n} rows")
            time.sleep(0.21)
        logger.info(f"opt_basic DONE: {total} rows, {int(time.time()-t0)}s")
        return {"status":"success","written":total,"elapsed":time.time()-t0}
