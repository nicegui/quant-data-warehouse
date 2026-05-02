"""个股资金流 — FundFlowCollector

AKShare collector for stock_individual_fund_flow(stock, market).
Per-stock pull (~120 rows), dedup by (stock_code, trade_date).
Checkpoint enabled: resumes from last trade_date per stock.
"""
from __future__ import annotations

import json
from typing import Any

from src.collectors.base import BaseAKShareCollector
from src.models.fund_flow import RawFundFlow


class FundFlowCollector(BaseAKShareCollector):
    """个股资金流 collector via akshare stock_individual_fund_flow()."""

    def __init__(self):
        super().__init__("fund_flow")

    # ── Checkpoint: resume from last trade_date ──

    @property
    def checkpoint_key(self) -> str:
        return "trade_date"

    # ── Fetch ──

    def fetch(self, stock: str = "000001", market: str = "sz", **kwargs) -> list[dict[str, Any]]:
        """Fetch individual stock fund flow from akshare.

        Args:
            stock: stock code string, e.g. "000001".
            market: market identifier, "sz" or "sh".
        """
        rows = self._ak_fetch(self.ak.stock_individual_fund_flow, stock=stock, market=market)
        # AKShare API does not return stock_code in the response; inject it
        for row in rows:
            row["_stock_code"] = stock
        return rows

    # ── Validate: Chinese → English field mapping ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese akshare columns to RawFundFlow fields."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = {
                "stock_code": self._safe_str(row.pop("_stock_code", "")),
                "trade_date": self._safe_str(row.get("日期")),
                "close": self._safe_float(row.get("收盘价")),
                "pct_chg": self._safe_float(row.get("涨跌幅")),
                "main_net": self._safe_float(row.get("主力净流入-净额")),
                "main_pct": self._safe_float(row.get("主力净流入-净占比")),
                "super_large_net": self._safe_float(row.get("超大单净流入-净额")),
                "super_large_pct": self._safe_float(row.get("超大单净流入-净占比")),
                "large_net": self._safe_float(row.get("大单净流入-净额")),
                "large_pct": self._safe_float(row.get("大单净流入-净占比")),
                "medium_net": self._safe_float(row.get("中单净流入-净额")),
                "medium_pct": self._safe_float(row.get("中单净流入-净占比")),
                "small_net": self._safe_float(row.get("小单净流入-净额")),
                "small_pct": self._safe_float(row.get("小单净流入-净占比")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    # ── Store ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records, deduplicating by (stock_code, trade_date)."""
        if not records:
            return 0
        return self._store_dedup(RawFundFlow, records, ["stock_code", "trade_date"])
