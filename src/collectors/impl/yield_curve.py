"""国债收益率曲线 — YieldCurveCollector

Tushare yc_cb API.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.bond import RawYcCb
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class YieldCurveCollector(BaseTushareCollector):
    """国债收益率曲线 collector."""

    def __init__(self, token: str):
        super().__init__("yc_cb", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              curve_type: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        if curve_type:
            params["curve_type"] = curve_type
        return self.api_call("yc_cb", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "curve_name": row.get("curve_name"),
                "curve_type": row.get("curve_type"),
                "curve_term": _f(row.get("curve_term")),
                "yield_": _f(row.get("yield")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawYcCb, records, ["trade_date", "ts_code", "curve_type", "curve_term"])
