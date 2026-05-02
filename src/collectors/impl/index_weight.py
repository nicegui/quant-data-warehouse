"""指数成分权重 — IndexWeightCollector

Tushare index_weight API — 月度权重数据.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RawIndexWeight
from src.collectors.base import BaseTushareCollector


class IndexWeightCollector(BaseTushareCollector):
    """指数成分权重 collector."""

    def __init__(self, token: str):
        super().__init__("index_weight", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, index_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (index_code or trade_date):
            index_code = "000300.SH"
        if index_code:
            params["index_code"] = index_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("index_weight", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "index_code": row.get("index_code", ""),
                "con_code": row.get("con_code", ""),
                "trade_date": row.get("trade_date"),
                "weight": row.get("weight"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawIndexWeight).filter_by(
                    index_code=rec["index_code"],
                    con_code=rec["con_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawIndexWeight(**rec))
                written += 1
        return written

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
                raw = self.fetch(index_code=ts_code, start_date="19900101", end_date="20260502")
                if raw:
                    total += self.store_raw(self.validate(raw))
            except Exception as e:
                logger.error(f"[{ts_code}] ERROR: {e}"); errors += 1
            if (i+1) % 200 == 0:
                logger.info(f"[{i+1}/{len(indices)}] {total:,} rows | {(i+1)/(time.time()-t0):.1f} idx/s")
            time.sleep(0.21)
        logger.info(f"index_weight DONE: {len(indices)} indices, {total:,} rows, {errors} err, {int(time.time()-t0)}s")
        return {"status":"success","indices":len(indices),"written":total,"errors":errors,"elapsed":time.time()-t0}
