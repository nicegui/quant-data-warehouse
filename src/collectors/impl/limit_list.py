"""涨停板列表 — LimitListCollector

Tushare limit_list_d API.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawLimitList
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class LimitListCollector(BaseTushareCollector):
    """涨停板列表 collector."""

    def __init__(self, token: str):
        super().__init__("limit_list", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", limit_type: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if limit_type:
            params["limit_type"] = limit_type
        return self.api_call("limit_list_d", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name"),
                "industry": row.get("industry"),
                "limit_type": row.get("limit_type"),
                "open_vol": _f(row.get("open_vol")),
                "close_vol": _f(row.get("close_vol")),
                "open_amt": _f(row.get("open_amt")),
                "close_amt": _f(row.get("close_amt")),
                "first_time": row.get("first_time"),
                "last_time": row.get("last_time"),
                "limit_times": int(row.get("limit_times", 0)) if (row.get("limit_times") is not None and row.get("limit_times") == row.get("limit_times")) else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawLimitList, records, ["ts_code", "trade_date"])
