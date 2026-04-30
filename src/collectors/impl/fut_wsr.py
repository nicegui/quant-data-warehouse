"""期货仓单 — FutWsrCollector

Tushare fut_wsr API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.futures import RawFutWsr
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FutWsrCollector(BaseTushareCollector):
    """期货仓单 collector."""

    def __init__(self, token: str):
        super().__init__("fut_wsr", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", symbol: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if symbol:
            params["symbol"] = symbol
        return self.api_call("fut_wsr", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "symbol": row.get("symbol", ""),
                "fut_name": row.get("fut_name"),
                "warehouse": row.get("warehouse"),
                "pre_vol": _f(row.get("pre_vol")),
                "vol": _f(row.get("vol")),
                "vol_chg": _f(row.get("vol_chg")),
                "unit": row.get("unit"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFutWsr).filter_by(
                    trade_date=rec["trade_date"],
                    symbol=rec["symbol"],
                    warehouse=rec["warehouse"],
                ).first()
                if existing:
                    continue
                session.add(RawFutWsr(**rec))
                written += 1
        return written
