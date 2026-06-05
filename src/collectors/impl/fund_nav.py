"""基金净值 — FundNavCollector

Tushare fund_nav API — 基金净值数据.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.fund import RawFundNav
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundNavCollector(BaseTushareCollector):
    """基金净值 collector.

    API: pro.fund_nav(ts_code=..., nav_date=..., end_date=...)
    Fields: ts_code, ann_date, nav_date, unit_nav, accum_nav, adj_nav
    """

    def __init__(self, token: str):
        super().__init__("fund_nav", token)

    @property
    def checkpoint_key(self):
        return "nav_date"

    def fetch(self, nav_date: str = "", ts_code: str = "", end_date: str = "", **kwargs) -> list[dict]:
        nd = nav_date or dt.now().strftime("%Y%m%d")
        params: dict[str, Any] = {"nav_date": nd}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fund_nav", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "nav_date": row.get("nav_date"),
                "unit_nav": _f(row.get("unit_nav")),
                "accum_nav": _f(row.get("accum_nav")),
                "adj_nav": _f(row.get("adj_nav")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFundNav, records, ["ts_code", "nav_date"])
