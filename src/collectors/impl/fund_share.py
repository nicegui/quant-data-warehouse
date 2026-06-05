"""基金规模 — FundShareCollector

Tushare fund_share API.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fund import RawFundShare
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundShareCollector(BaseTushareCollector):
    """基金规模 collector."""

    def __init__(self, token: str):
        super().__init__("fund_share", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fund_share", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "fd_share": _f(row.get("fd_share")),
                "fund_type": row.get("fund_type", ""),
                "market": row.get("market", ""),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFundShare, records, ["ts_code", "trade_date"])
