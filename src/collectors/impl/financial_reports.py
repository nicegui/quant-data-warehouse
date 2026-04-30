"""财报 — FinancialReportCollector

Tushare income/vf_income, balance_sheet, cashflow APIs.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawFinancialReports
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FinancialReportCollector(BaseTushareCollector):
    """财务报表 collector (利润表/资产负债表/现金流量表)."""

    def __init__(self, token: str):
        super().__init__("financial_reports", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, end_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        params = {}
        if not (ts_code or end_date):
            ts_code = "000001.SZ"
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("income", **params)

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
                "total_revenue": _f(row.get("total_revenue")),
                "revenue": _f(row.get("revenue")),
                "oper_cost": _f(row.get("oper_cost")),
                "total_profit": _f(row.get("total_profit")),
                "n_income": _f(row.get("n_income")),
                "n_income_attr_p": _f(row.get("n_income_attr_p")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialReports).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                    report_type=rec.get("report_type"),
                ).first()
                if existing:
                    continue
                session.add(RawFinancialReports(**rec))
                written += 1
        return written
