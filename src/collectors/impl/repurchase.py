"""股票回购 — RepurchaseCollector

Tushare repurchase API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawRepurchase
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class RepurchaseCollector(BaseTushareCollector):
    """股票回购 collector."""

    def __init__(self, token: str):
        super().__init__("repurchase", token)

    @property
    def checkpoint_key(self):
        return "ann_date"

    def fetch(self, ts_code: str = "", ann_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("repurchase", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "proc": row.get("proc"),
                "exp_date": row.get("exp_date"),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "high_limit": _f(row.get("high_limit")),
                "low_limit": _f(row.get("low_limit")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawRepurchase, records, ["ts_code", "ann_date", "end_date"])
