"""基金分红 — FundDivCollector

Tushare fund_div API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.fund import RawFundDiv
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundDivCollector(BaseTushareCollector):
    """基金分红 collector."""

    def __init__(self, token: str):
        super().__init__("fund_div", token)

    @property
    def checkpoint_key(self):
        return "ann_date"

    def fetch(self, ts_code: str = "", ann_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (ts_code or ann_date):
            from datetime import date, timedelta
            ann_date = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("fund_div", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "imp_anndate": row.get("imp_anndate"),
                "base_date": row.get("base_date"),
                "div_proc": row.get("div_proc"),
                "record_date": row.get("record_date"),
                "ex_date": row.get("ex_date"),
                "pay_date": row.get("pay_date"),
                "earpay_date": row.get("earpay_date"),
                "net_ex_date": row.get("net_ex_date"),
                "div_cash": _f(row.get("div_cash")),
                "base_unit": _f(row.get("base_unit")),
                "ear_distr": _f(row.get("ear_distr")),
                "ear_amount": _f(row.get("ear_amount")),
                "account_date": row.get("account_date"),
                "base_year": row.get("base_year"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFundDiv).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFundDiv(**rec))
                written += 1
        return written
