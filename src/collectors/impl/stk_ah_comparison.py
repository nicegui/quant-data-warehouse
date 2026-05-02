"""AH股比价 — StkAhComparisonCollector

Tushare stk_ah_comparison API — AH股比价数据。
按trade_date全量获取（单日~150行，远低于1000限制）。
数据从20250812开始，串行遍历交易日。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.hk_market import RawStkAhComparison
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class StkAhComparisonCollector(BaseTushareCollector):
    """AH股比价 collector — 按日全量获取."""

    def __init__(self, token: str):
        super().__init__("stk_ah_comparison", token)

    @property
    def checkpoint_key(self) -> str:
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        params.update({k: v for k, v in kwargs.items() if v})
        return self.api_call("stk_ah_comparison", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "hk_code": row.get("hk_code", ""),
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "hk_name": row.get("hk_name"),
                "hk_pct_chg": _f(row.get("hk_pct_chg")),
                "hk_close": _f(row.get("hk_close")),
                "name": row.get("name"),
                "close": _f(row.get("close")),
                "pct_chg": _f(row.get("pct_chg")),
                "ah_comparison": _f(row.get("ah_comparison")),
                "ah_premium": _f(row.get("ah_premium")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkAhComparison).filter_by(
                    hk_code=rec["hk_code"],
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkAhComparison(**rec))
                written += 1
        return written

    def run(self, **kwargs) -> dict:
        """按交易日全量获取 AH 比价数据。"""
        # Get trading dates since 20250812
        try:
            cal = self.pro.trade_cal(
                exchange="SSE",
                start_date="20250812",
                end_date="20261231",
                is_open="1",
            )
            dates = sorted(cal["cal_date"].tolist())
        except Exception as e:
            logger.error("Failed to get trade cal: %s", e)
            return {"status": "failed", "error": str(e)}

        existing_dates: set[str] = set()
        try:
            with db_session() as session:
                rows = session.query(RawStkAhComparison.trade_date).distinct().all()
                existing_dates = {r[0] for r in rows if r[0]}
        except Exception:
            pass

        pending = [d for d in dates if d not in existing_dates]
        if not pending:
            logger.info("ah_comparison: all dates up to date")
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("ah_comparison: %d dates pending", len(pending))

        total_fetched, total_written, total_errors = 0, 0, 0
        t0 = time.time()

        for i, d in enumerate(pending):
            try:
                raw = self.fetch(trade_date=d)
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch(trade_date=d)
                else:
                    total_errors += 1
                    continue

            if raw:
                validated = self.validate(raw)
                written = self.store_raw(validated)
                total_fetched += len(raw)
                total_written += written

            if (i + 1) % 50 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info("[%d/%d] %s +%d rows | %.1f/s",
                            i + 1, len(pending), d, total_written, rate)

            time.sleep(0.25)

        return {
            "status": "success" if total_errors == 0 else "partial",
            "fetched": total_fetched,
            "written": total_written,
            "errors": total_errors,
        }
