"""结算参数 — FutSettleCollector

Tushare fut_settle API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.futures import RawFutSettle
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FutSettleCollector(BaseTushareCollector):
    """结算参数 collector."""

    def __init__(self, token: str):
        super().__init__("fut_settle", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (trade_date or ts_code):
            from datetime import date, timedelta
            trade_date = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fut_settle", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "settle": _f(row.get("settle")),
                "trading_fee_rate": _f(row.get("trading_fee_rate")),
                "trading_fee": _f(row.get("trading_fee")),
                "delivery_fee": _f(row.get("delivery_fee")),
                "b_hedging_margin_rate": _f(row.get("b_hedging_margin_rate")),
                "s_hedging_margin_rate": _f(row.get("s_hedging_margin_rate")),
                "long_margin_rate": _f(row.get("long_margin_rate")),
                "short_margin_rate": _f(row.get("short_margin_rate")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFutSettle).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFutSettle(**rec))
                written += 1
        return written
