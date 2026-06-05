"""基金/ETF — FundCollector

fund_daily + fund_portfolio from Tushare API.
"""

from __future__ import annotations

from typing import Any
from datetime import datetime as dt

from src.db.session import db_session
from src.models.fund import RawFundDaily, RawFundPortfolio
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundCollector(BaseTushareCollector):
    """基金/ETF collector."""

    def __init__(self, token: str):
        super().__init__("fund", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        return self.api_call("fund_daily", trade_date=td)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "close": _f(row.get("close")),
                "pre_close": _f(row.get("pre_close")),
                "change": _f(row.get("change")),
                "pct_chg": _f(row.get("pct_chg")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawFundDaily, records, ["ts_code", "trade_date"])


    def fetch_fund_portfolio(self, ts_code: str) -> list[dict]:
        return self.api_call("fund_portfolio", ts_code=ts_code)

    def store_fund_portfolio(self, records: list[dict]) -> int:
        return self._store_dedup(RawFundPortfolio, records, ["ts_code", "end_date", "symbol"])
