"""每日基本面 — DailyBasicCollector

Tushare daily_basic API — PE/PB/换手率/市值.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.market import RawDailyBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class DailyBasicCollector(BaseTushareCollector):
    """每日基本面指标 collector."""

    def __init__(self, token: str):
        super().__init__("daily_basic", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("daily_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "close": _f(row.get("close"), 0),
                "turnover_rate": _f(row.get("turnover_rate")),
                "turnover_rate_f": _f(row.get("turnover_rate_f")),
                "volume_ratio": _f(row.get("volume_ratio")),
                "pe": _f(row.get("pe")),
                "pe_ttm": _f(row.get("pe_ttm")),
                "pb": _f(row.get("pb")),
                "ps": _f(row.get("ps")),
                "ps_ttm": _f(row.get("ps_ttm")),
                "dv_ratio": _f(row.get("dv_ratio")),
                "dv_ttm": _f(row.get("dv_ttm")),
                "total_mv": _f(row.get("total_mv")),
                "circ_mv": _f(row.get("circ_mv")),
                "total_share": _f(row.get("total_share")),
                "float_share": _f(row.get("float_share")),
                "free_share": _f(row.get("free_share")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawDailyBasic, records, ["ts_code", "trade_date"])
