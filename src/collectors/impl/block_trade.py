"""大宗交易 — BlockTradeCollector

Tushare block_trade API — 大宗交易数据.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.market import RawBlockTrade
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class BlockTradeCollector(BaseTushareCollector):
    """大宗交易 collector."""

    def __init__(self, token: str):
        super().__init__("block_trade", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("block_trade", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "price": _f(row.get("price")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "buyer": row.get("buyer", ""),
                "seller": row.get("seller", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawBlockTrade, records, ["ts_code", "trade_date", "buyer", "seller"])
