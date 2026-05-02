"""期货 — FuturesCollector

fut_daily + fut_holding from Tushare API.
"""

from __future__ import annotations

from typing import Any
from datetime import datetime as dt

from src.db.session import db_session
from src.models.futures import RawFutDaily, RawFutHolding
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FuturesCollector(BaseTushareCollector):
    """期货 collector."""

    def __init__(self, token: str):
        super().__init__("futures", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", start_date: str = "", end_date: str = "", exchange: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if exchange:
            params["exchange"] = exchange
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if not (start_date or end_date):
            if trade_date:
                params["trade_date"] = trade_date
            elif not params:
                params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("fut_daily", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "pre_close": _f(row.get("pre_close")),
                "pre_settle": _f(row.get("pre_settle")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "close": _f(row.get("close")),
                "settle": _f(row.get("settle")),
                "change1": _f(row.get("change1")),
                "change2": _f(row.get("change2")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "oi": _f(row.get("oi")),
                "oi_chg": _f(row.get("oi_chg")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFutDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFutDaily(**rec))
                written += 1
        return written

    # ── 期货会员持仓 (separate fetch, not using run()) ──

    def fetch_fut_holding(self, trade_date: str = "", symbol: str = "") -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if symbol:
            params["symbol"] = symbol
        return self.api_call("fut_holding", **params)

    def store_fut_holding(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFutHolding).filter_by(
                    trade_date=rec["trade_date"],
                    symbol=rec["symbol"],
                    broker=rec["broker"],
                ).first()
                if existing:
                    continue
                session.add(RawFutHolding(**rec))
                written += 1
        return written
