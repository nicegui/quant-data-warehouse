"""可转债基本信息 — CbBasicCollector

Tushare cb_basic API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.convertible_bond import RefCbBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CbBasicCollector(BaseTushareCollector):
    """可转债基本信息 collector — 全量更新."""

    def __init__(self, token: str):
        super().__init__("cb_basic", token)

    def fetch(self, ts_code: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("cb_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "bond_full_name": row.get("bond_full_name"),
                "bond_short_name": row.get("bond_short_name"),
                "cb_type": row.get("cb_type"),
                "cb_code": row.get("cb_code"),
                "stk_code": row.get("stk_code"),
                "stk_short_name": row.get("stk_short_name"),
                "maturity": _f(row.get("maturity")),
                "par": _f(row.get("par")),
                "issue_price": _f(row.get("issue_price")),
                "issue_size": _f(row.get("issue_size")),
                "remain_size": _f(row.get("remain_size")),
                "value_date": row.get("value_date"),
                "maturity_date": row.get("maturity_date"),
                "rate_type": row.get("rate_type"),
                "coupon_rate": _f(row.get("coupon_rate")),
                "add_rate": _f(row.get("add_rate")),
                "pay_per_year": row.get("pay_per_year"),
                "list_date": row.get("list_date"),
                "delist_date": row.get("delist_date"),
                "exchange": row.get("exchange"),
                "conv_start_date": row.get("conv_start_date"),
                "conv_end_date": row.get("conv_end_date"),
                "conv_stop_date": row.get("conv_stop_date"),
                "first_conv_price": _f(row.get("first_conv_price")),
                "conv_price": _f(row.get("conv_price")),
                "rate_clause": row.get("rate_clause"),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefCbBasic, records, ["ts_code"])
