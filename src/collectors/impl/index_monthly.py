"""指数月线 — IndexMonthlyCollector"""
from __future__ import annotations
from src.db.session import db_session
from src.models.market import RawIndexMonthly
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class IndexMonthlyCollector(BaseTushareCollector):
    def __init__(self, token): super().__init__("index_monthly", token)
    @property
    def checkpoint_key(self): return "trade_date"
    def fetch(self, ts_code="", trade_date="", start_date="", end_date="", **kw):
        p={}
        if ts_code:p["ts_code"]=ts_code
        if trade_date:p["trade_date"]=trade_date
        if start_date:p["start_date"]=start_date
        if end_date:p["end_date"]=end_date
        if not p:
            from datetime import date, timedelta
            p["trade_date"]=(date.today()-timedelta(days=1)).strftime("%Y%m%d")
        return self.api_call("index_monthly",**p)
    def validate(self, raw):
        r=[]
        ohcl=("close","open","high","low","pre_close","change","pct_chg","vol","amount")
        for x in raw:
            r.append({k:_f(x.get(k))if k in ohcl else x.get(k)for k in("ts_code","trade_date","close","open","high","low","pre_close","change","pct_chg","vol","amount")})
        return r
    def store_raw(self,recs):
        w=0
        with db_session()as s:
            for r in recs:
                e=s.query(RawIndexMonthly).filter_by(ts_code=r["ts_code"],trade_date=r["trade_date"]).first()
                if not e:s.add(RawIndexMonthly(**r));w+=1
        return w

    def run(self) -> dict:
        import time, logging
        from sqlalchemy import text
        from src.db.session import get_session
        logger = logging.getLogger(__name__)
        t0 = time.time()
        total, errors = 0, 0
        session = get_session()
        indices = [r[0] for r in session.execute(text("SELECT ts_code FROM ref_index_basic")).fetchall()]
        session.close()
        logger.info(f"Found {len(indices)} index codes")
        for i, ts_code in enumerate(indices):
            try:
                raw = self.fetch(ts_code=ts_code, start_date="19900101", end_date="20260502")
                if raw:
                    total += self.store_raw(self.validate(raw))
            except Exception as e:
                logger.error(f"[{ts_code}] ERROR: {e}"); errors += 1
            if (i+1) % 500 == 0:
                logger.info(f"[{i+1}/{len(indices)}] {total:,} rows | {(i+1)/(time.time()-t0):.1f} idx/s")
            time.sleep(0.21)
        logger.info(f"index_monthly DONE: {len(indices)} indices, {total:,} rows, {errors} err, {int(time.time()-t0)}s")
        return {"status":"success","indices":len(indices),"written":total,"errors":errors,"elapsed":time.time()-t0}
