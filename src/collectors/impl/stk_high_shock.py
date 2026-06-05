"""个股严重异常波动 — StkHighShockCollector

Tushare stk_high_shock API — 交易所每日发布的个股严重异常波动情况。
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawStkHighShock
from src.collectors.base import BaseTushareCollector


class StkHighShockCollector(BaseTushareCollector):
    """个股严重异常波动 collector."""

    def __init__(self, token: str):
        super().__init__("stk_high_shock", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
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
        return self.api_call("stk_high_shock", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "name": row.get("name"),
                "trade_market": row.get("trade_market"),
                "reason": row.get("reason"),
                "period": row.get("period"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStkHighShock, records, ["ts_code", "trade_date", "period"])
