"""期货会员持仓 — FutHoldingCollector

Tushare fut_holding API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.futures import RawFutHolding
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FutHoldingCollector(BaseTushareCollector):
    """期货会员持仓 collector."""

    def __init__(self, token: str):
        super().__init__("fut_holding", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", symbol: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (trade_date or symbol):
            from datetime import date, timedelta
            trade_date = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        if trade_date:
            params["trade_date"] = trade_date
        if symbol:
            params["symbol"] = symbol
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fut_holding", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "symbol": row.get("symbol", ""),
                "broker": row.get("broker", ""),
                "vol": _f(row.get("vol")),
                "vol_chg": _f(row.get("vol_chg")),
                "long_hld": _f(row.get("long_hld")),
                "long_chg": _f(row.get("long_chg")),
                "short_hld": _f(row.get("short_hld")),
                "short_chg": _f(row.get("short_chg")),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFutHolding, records, ["trade_date", "symbol", "broker"])
