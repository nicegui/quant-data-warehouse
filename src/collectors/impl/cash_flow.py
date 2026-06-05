"""现金流量表 — CashFlowCollector

Tushare cashflow API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawCashFlow
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CashFlowCollector(BaseTushareCollector):
    """现金流量表 collector."""

    def __init__(self, token: str):
        super().__init__("cash_flow", token)

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
        return self.api_call("cashflow", **params)

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
                "cash_recp_sg": _f(row.get("cash_recp_sg")),
                "cash_pay_acq": _f(row.get("cash_pay_acq")),
                "cash_pay_beh_empl": _f(row.get("cash_pay_beh_empl")),
                "st_cash_out_act": _f(row.get("st_cash_out_act")),
                "st_cash_in_act": _f(row.get("st_cash_in_act")),
                "n_cashflow_act": _f(row.get("n_cashflow_act")),
                "n_cashflow_inv_act": _f(row.get("n_cashflow_inv_act")),
                "n_cashflow_fin_act": _f(row.get("n_cashflow_fin_act")),
                "n_incr_cash": _f(row.get("n_incr_cash")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawCashFlow, records, ["ts_code", "end_date", "report_type"])
