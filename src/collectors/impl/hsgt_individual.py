"""北向资金个股持股 — HsgtIndividualCollector

AKShare collector for stock_hsgt_individual_em(symbol=...).
Returns historical northbound holding data for a single A-share stock.
"""
from __future__ import annotations

import json
from typing import Any

from src.collectors.base import BaseAKShareCollector
from src.models.hsgt_individual import RawHsgtIndividual


class HsgtIndividualCollector(BaseAKShareCollector):
    """北向资金个股持股明细 via akshare stock_hsgt_individual_em()."""

    def __init__(self):
        super().__init__("hsgt_individual")

    # ── Fetch ──

    def fetch(self, symbol: str = "002008", **kwargs) -> list[dict[str, Any]]:
        """Fetch northbound holding history for a stock.

        Args:
            symbol: A-share stock code (e.g. "002008", "600519").
        """
        return self._ak_fetch(self.ak.stock_hsgt_individual_em, symbol=symbol)

    # ── Validate: Chinese → English field mapping ──

    def validate(self, raw: list[dict[str, Any]], symbol: str = "002008") -> list[dict[str, Any]]:
        """Normalize Chinese akshare columns to RawHsgtIndividual fields.

        Extracts stock_code from the symbol parameter (not present in the
        DataFrame returned by akshare).
        """
        if not raw:
            return []

        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = {
                "stock_code": symbol,
                "trade_date": self._safe_str(row.get("持股日期")),
                "close": self._safe_float(row.get("当日收盘价")),
                "pct_chg": self._safe_float(row.get("当日涨跌幅")),
                "hold_shares": self._safe_float(row.get("持股数量")),
                "hold_value": self._safe_float(row.get("持股市值")),
                "hold_pct": self._safe_float(row.get("持股数量占A股百分比")),
                "delta_shares": self._safe_float(row.get("今日增持股数")),
                "delta_value": self._safe_float(row.get("今日增持资金")),
                "delta_market_value": self._safe_float(row.get("今日持股市值变化")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    # ── Store ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Dedup by (stock_code, trade_date)."""
        if not records:
            return 0
        return self._store_dedup(RawHsgtIndividual, records, ["stock_code", "trade_date"])
