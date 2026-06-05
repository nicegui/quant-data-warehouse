"""业绩预告 — ForecastCollector

Tushare forecast API — 上市公司业绩预告数据.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawForecast
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ForecastCollector(BaseTushareCollector):
    """业绩预告 collector."""

    def __init__(self, token: str):
        super().__init__("forecast", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", end_date: str = "", ann_date: str = "",
              **kwargs) -> list[dict]:
        params = {}
        if not (ts_code or ann_date or end_date):
            from datetime import date, timedelta
            ann_date = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("forecast", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "type": row.get("type"),
                "p_change_min": _f(row.get("p_change_min")),
                "p_change_max": _f(row.get("p_change_max")),
                "net_profit_min": _f(row.get("net_profit_min")),
                "net_profit_max": _f(row.get("net_profit_max")),
                "last_parent_net": _f(row.get("last_parent_net")),
                "first_ann_date": row.get("first_ann_date"),
                "summary": row.get("summary"),
                "change_reason": row.get("change_reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawForecast, records, ["ts_code", "end_date"])
