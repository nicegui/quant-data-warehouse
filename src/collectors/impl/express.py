"""业绩快报 — ExpressCollector

Tushare express API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawExpress
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ExpressCollector(BaseTushareCollector):
    """业绩快报 collector."""

    def __init__(self, token: str):
        super().__init__("express", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, end_date: str = "", ts_code: str = "", ann_date: str = "", **kwargs) -> list[dict]:
        params = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("express", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "revenue": _f(row.get("revenue")),
                "operate_profit": _f(row.get("operate_profit")),
                "total_profit": _f(row.get("total_profit")),
                "n_income": _f(row.get("n_income")),
                "total_assets": _f(row.get("total_assets")),
                "total_hldr_eqy_exc_min_int": _f(row.get("total_hldr_eqy_exc_min_int")),
                "diluted_eps": _f(row.get("diluted_eps")),
                "diluted_roe": _f(row.get("diluted_roe")),
                "yoy_net_profit": _f(row.get("yoy_net_profit")),
                "bps": _f(row.get("bps")),
                "perf_summary": row.get("perf_summary"),
                "update_flag": row.get("update_flag"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawExpress, records, ["ts_code", "end_date"])
