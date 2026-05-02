"""申万行业指数日线 — SwDailyCollector

pro.sw_daily API: ts_code, trade_date, name, open, high, low, close,
                   change, pct_change, vol, amount, pe, pb, float_mv, total_mv
"""
from __future__ import annotations
from src.db.session import db_session
from src.models.index import RawSwDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class SwDailyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("sw_daily", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code: p["ts_code"]=ts_code
        if trade_date: p["trade_date"]=trade_date
        if start_date: p["start_date"]=start_date
        if end_date: p["end_date"]=end_date
        return self.api_call("sw_daily",**p)
    def validate(self, raw):
        r=[]
        nf=("open","high","low","close","change","pct_change","vol","amount","pe","pb","float_mv","total_mv")
        for x in raw:
            r.append({k:_f(x.get(k))if k in nf else x.get(k)for k in("ts_code","trade_date","name","open","high","low","close","change","pct_change","vol","amount","pe","pb","float_mv","total_mv")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawSwDaily).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawSwDaily(**r));w+=1
        return w

    def run(self) -> dict:
        import time, logging
        from datetime import datetime, timedelta
        logger = logging.getLogger(__name__)
        t0 = time.time(); total, errors, days = 0, 0, 0
        d = datetime(2020,1,1); end = datetime(2026,5,3)
        while d <= end:
            try:
                raw = self.fetch(trade_date=d.strftime("%Y%m%d"))
                if raw:
                    total += self.store_raw(self.validate(raw))
                days += 1
            except Exception as e:
                logger.error(f"[{d}] ERROR: {e}"); errors += 1
            d += timedelta(days=1)
            if days % 200 == 0:
                logger.info(f"[{d}] {days} days, {total:,} rows | {days/(time.time()-t0):.1f} d/s")
            time.sleep(0.21)
        logger.info(f"sw_daily DONE: {days} days, {total:,} rows, {errors} err, {int(time.time()-t0)}s")
        return {"status":"success","written":total,"days":days,"errors":errors,"elapsed":time.time()-t0}
