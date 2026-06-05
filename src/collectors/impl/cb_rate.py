"""可转债利率 — CbRateCollector

Tushare cb_rate API.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.convertible_bond import RawCbRate
from src.collectors.base import BaseTushareCollector


class CbRateCollector(BaseTushareCollector):
    """可转债利率 collector — 全量更新."""

    def __init__(self, token: str):
        super().__init__("cb_rate", token)

    def fetch(self, ts_code: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("cb_rate", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawCbRate, records, ["ts_code"])
