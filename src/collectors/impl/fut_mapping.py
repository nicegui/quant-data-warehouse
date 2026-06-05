"""主力合约映射 — FutMappingCollector

Tushare fut_mapping API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.futures import RawFutMapping
from src.collectors.base import BaseTushareCollector


class FutMappingCollector(BaseTushareCollector):
    """主力合约映射 collector."""

    def __init__(self, token: str):
        super().__init__("fut_mapping", token)

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
        return self.api_call("fut_mapping", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "mapping_ts_code": row.get("mapping_ts_code", ""),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFutMapping, records, ["ts_code", "trade_date"])
