"""基金复权因子 — FundAdjCollector

Tushare fund_adj API.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.fund import RawFundAdj
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundAdjCollector(BaseTushareCollector):
    """基金复权因子 collector."""

    def __init__(self, token: str):
        super().__init__("fund_adj", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fund_adj", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "adj_factor": _f(row.get("adj_factor")),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFundAdj, records, ["ts_code", "trade_date"])
