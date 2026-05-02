"""期权日线 — OptDailyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.opt_market import RawOptDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class OptDailyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("opt_daily", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        return self.api_call("opt_daily",**p)
    def validate(self, raw):
        r=[]
        nf=("pre_settle","pre_close","open","high","low","close","settle","vol","amount","oi")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","trade_date","exchange","pre_settle","pre_close","open","high","low","close","settle","vol","amount","oi")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawOptDaily).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawOptDaily(**r));w+=1
        return w

    def run(self) -> dict:
        import time, logging
        from datetime import datetime, timedelta
        logger = logging.getLogger(__name__)
        t0 = time.time(); total, errors, days = 0, 0, 0
        d = datetime(2020,1,1); end = datetime(2026,5,3)
        while d <= end:
            ds = d.strftime("%Y%m%d")
            try:
                raw = self.fetch(trade_date=ds)
                if raw: total += self.store_raw(self.validate(raw))
                days += 1
            except Exception as e:
                logger.error(f"[{ds}] ERROR: {e}"); errors += 1
            d += timedelta(days=1)
            if days % 200 == 0:
                logger.info(f"[{ds}] {days} days, {total:,} rows | {days/(time.time()-t0):.1f} d/s")
            time.sleep(0.21)
        logger.info(f"opt_daily DONE: {days} days, {total:,} rows, {errors} err, {int(time.time()-t0)}s")
        return {"status":"success","written":total,"days":days,"errors":errors,"elapsed":time.time()-t0}
