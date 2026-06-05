"""资产负债表 — BalanceSheetCollector

Tushare balancesheet API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawBalanceSheet
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class BalanceSheetCollector(BaseTushareCollector):
    """资产负债表 collector."""

    def __init__(self, token: str):
        super().__init__("balance_sheet", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, end_date: str = "", ts_code: str = "", report_type: str = "", **kwargs) -> list[dict]:
        params = {}
        if not (ts_code or end_date):
            ts_code = "000001.SZ"
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        if report_type:
            params["report_type"] = report_type
        return self.api_call("balancesheet", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "f_ann_date": row.get("f_ann_date"),
                "end_date": row.get("end_date"),
                "report_type": row.get("report_type"),
                "comp_type": row.get("comp_type"),
                "total_assets": _f(row.get("total_assets")),
                "total_liab": _f(row.get("total_liab")),
                "total_hldr_eqy_exc_min_int": _f(row.get("total_hldr_eqy_exc_min_int")),
                "total_cur_assets": _f(row.get("total_cur_assets")),
                "total_cur_liab": _f(row.get("total_cur_liab")),
                "goodwill": _f(row.get("goodwill")),
                "inventories": _f(row.get("inventories")),
                "accounts_receiv": _f(row.get("accounts_receiv")),
                "notes_receiv": _f(row.get("notes_receiv")),
                "fix_assets": _f(row.get("fix_assets")),
                "total_nca": _f(row.get("total_nca")),
                "notes_payable": _f(row.get("notes_payable")),
                "accounts_payable": _f(row.get("accounts_payable")),
                "long_borrow": _f(row.get("long_borrow")),
                "short_borrow": _f(row.get("short_borrow")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawBalanceSheet, records, ["ts_code", "end_date", "report_type"])
