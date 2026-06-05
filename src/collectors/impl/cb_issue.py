"""可转债发行 — CbIssueCollector

Tushare cb_issue API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.convertible_bond import RawCbIssue
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CbIssueCollector(BaseTushareCollector):
    """可转债发行 collector."""

    def __init__(self, token: str):
        super().__init__("cb_issue", token)

    @property
    def checkpoint_key(self):
        return "ann_date"

    def fetch(self, ts_code: str = "", ann_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("cb_issue", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "res_ann_date": row.get("res_ann_date"),
                "plan_issue_size": _f(row.get("plan_issue_size")),
                "issue_size": _f(row.get("issue_size")),
                "issue_price": _f(row.get("issue_price")),
                "issue_type": row.get("issue_type"),
                "onl_code": row.get("onl_code"),
                "onl_name": row.get("onl_name"),
                "onl_date": row.get("onl_date"),
                "onl_size": _f(row.get("onl_size")),
                "onl_pch_vol": _f(row.get("onl_pch_vol")),
                "onl_pch_num": row.get("onl_pch_num"),
                "onl_pch_excess": _f(row.get("onl_pch_excess")),
                "shd_ration_code": row.get("shd_ration_code"),
                "shd_ration_name": row.get("shd_ration_name"),
                "shd_ration_date": row.get("shd_ration_date"),
                "shd_ration_record_date": row.get("shd_ration_record_date"),
                "shd_ration_pay_date": row.get("shd_ration_pay_date"),
                "shd_ration_price": _f(row.get("shd_ration_price")),
                "shd_ration_ratio": _f(row.get("shd_ration_ratio")),
                "shd_ration_size": _f(row.get("shd_ration_size")),
                "offl_size": _f(row.get("offl_size")),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawCbIssue, records, ["ts_code", "ann_date"])
