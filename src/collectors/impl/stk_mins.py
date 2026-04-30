"""股票分钟行情 — StkMinsCollector

Tushare stk_mins API — 1/5/15/30/60 min bars.
Rate-limited at 2 calls/min — use sparingly.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.market import RawStkMins
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkMinsCollector(BaseTushareCollector):
    """股票分钟行情 collector."""

    def __init__(self, token: str):
        super().__init__("stk_mins", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", freq: str = "5min", trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt

        td = trade_date or dt.now().strftime("%Y%m%d")
        if ts_code:
            return self.api_call("stk_mins", ts_code=ts_code, freq=freq, trade_date=td)
        return self.api_call("stk_mins", freq=freq, trade_date=td)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_time": row.get("trade_time"),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "close": _f(row.get("close")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkMins).filter_by(
                    ts_code=rec["ts_code"],
                    trade_time=rec["trade_time"],
                ).first()
                if existing:
                    continue
                session.add(RawStkMins(**rec))
                written += 1
        return written
