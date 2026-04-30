"""基金持仓 — FundPortfolioCollector

Tushare fund_portfolio API.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fund import RawFundPortfolio
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundPortfolioCollector(BaseTushareCollector):
    """基金持仓 collector."""

    def __init__(self, token: str):
        super().__init__("fund_portfolio", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", ann_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (ts_code or ann_date or end_date):
            from datetime import date, timedelta
            ann_date = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fund_portfolio", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "symbol": row.get("symbol", ""),
                "mkv": _f(row.get("mkv")),
                "amount": _f(row.get("amount")),
                "stk_mkv_ratio": _f(row.get("stk_mkv_ratio")),
                "stk_float_ratio": _f(row.get("stk_float_ratio")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFundPortfolio).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                    symbol=rec["symbol"],
                ).first()
                if existing:
                    continue
                session.add(RawFundPortfolio(**rec))
                written += 1
        return written
