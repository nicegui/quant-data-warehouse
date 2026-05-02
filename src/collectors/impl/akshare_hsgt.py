"""沪深港通资金流向 — AkshareHsgtCollector

Non-Tushare collector using akshare.stock_hsgt_hist_em().
"""
from __future__ import annotations

import json
from typing import Any

from src.models.akshare_macro import RawAkshareHsgtHist
from src.collectors.base import BaseAKShareCollector


class AkshareHsgtCollector(BaseAKShareCollector):
    """沪深港通历史资金流向 collector via akshare (non-Tushare)."""

    def __init__(self):
        super().__init__("akshare_hsgt")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch 沪深港通 historical fund flow from akshare."""
        return self._ak_fetch(self.ak.stock_hsgt_hist_em)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese field names to English."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            validated.append({
                "date_str": self._safe_str(row.get("日期")),
                "net_buy": self._safe_float(row.get("当日成交净买额")),
                "buy_amount": self._safe_float(row.get("买入成交额")),
                "sell_amount": self._safe_float(row.get("卖出成交额")),
                "cum_net_buy": self._safe_float(row.get("历史累计净买额")),
                "net_flow": self._safe_float(row.get("当日资金流入")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records, deduplicating by date_str."""
        return self._store_dedup(RawAkshareHsgtHist, records, ["date_str"])
