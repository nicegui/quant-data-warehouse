"""分红送股 — DividendCollector

Tushare dividend API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.corporate_action import RawDividend
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class DividendCollector(BaseTushareCollector):
    """分红送股 collector."""

    def __init__(self, token: str):
        super().__init__("dividend", token)

    @property
    def checkpoint_key(self):
        return "ann_date"

    def fetch(self, ts_code: str = "", ann_date: str = "", **kwargs) -> list[dict]:
        params = {}
        if not (ts_code or ann_date):
            from datetime import date, timedelta
            ann_date = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("dividend", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "ann_date": row.get("ann_date"),
                "div_proc": row.get("div_proc"),
                "stk_div": _f(row.get("stk_div")),
                "stk_bo_rate": _f(row.get("stk_bo_rate")),
                "stk_co_rate": _f(row.get("stk_co_rate")),
                "cash_div": _f(row.get("cash_div")),
                "cash_div_tax": _f(row.get("cash_div_tax")),
                "record_date": row.get("record_date"),
                "ex_date": row.get("ex_date"),
                "pay_date": row.get("pay_date"),
                "div_listdate": row.get("div_listdate"),
                "imp_ann_date": row.get("imp_ann_date"),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawDividend, records, ["ts_code", "ex_date"])
