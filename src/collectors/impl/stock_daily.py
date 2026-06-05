"""A股日线 — StockDailyCollector

Tushare daily API — 逐日行情数据 (OHLCV).
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.market import RawStockDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StockDailyCollector(BaseTushareCollector):
    """A股日线行情 collector."""

    def __init__(self, token: str):
        super().__init__("stock_daily", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("daily", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "open": _f(row.get("open"), 0),
                "high": _f(row.get("high"), 0),
                "low": _f(row.get("low"), 0),
                "close": _f(row.get("close"), 0),
                "pre_close": _f(row.get("pre_close"), 0),
                "change": _f(row.get("change"), 0),
                "pct_chg": _f(row.get("pct_chg"), 0),
                "vol": _f(row.get("vol"), 0),
                "amount": _f(row.get("amount"), 0),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStockDaily, records, ["ts_code", "trade_date"])
