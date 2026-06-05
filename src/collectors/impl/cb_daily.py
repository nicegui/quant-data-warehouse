"""可转债日线 — CbDailyCollector

Tushare cb_daily API — 可转债逐日行情数据 (OHLCV).
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.convertible_bond import RawCbDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CbDailyCollector(BaseTushareCollector):
    """可转债日线行情 collector."""

    def __init__(self, token: str):
        super().__init__("cb_daily", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if not (start_date or end_date):
            if trade_date:
                params["trade_date"] = trade_date
            elif not params:
                params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("cb_daily", **params)

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
        return self._store_dedup(RawCbDaily, records, ["ts_code", "trade_date"])
