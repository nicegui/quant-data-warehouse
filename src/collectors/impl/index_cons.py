"""指数成分股快照 — IndexConsCollector

Non-Tushare collector using akshare.index_stock_cons_csindex().
Each pull is a full snapshot — no checkpointing (always full pull).
"""

from __future__ import annotations

import json
from typing import Any

from src.models.index_cons import RawIndexCons
from src.collectors.base import BaseAKShareCollector


class IndexConsCollector(BaseAKShareCollector):
    """指数成分股 collector via akshare (non-Tushare).

    Supported index_code values:
      "000300" (沪深300), "000905" (中证500),
      "000016" (上证50), "399006" (创业板指), etc.
    """

    def __init__(self):
        super().__init__("index_cons")

    def fetch(self, index_code: str = "000300", **kwargs) -> list[dict[str, Any]]:
        """Fetch index constituent stocks from akshare.

        Args:
            index_code: index symbol, e.g. "000300" for 沪深300.
        """
        return self._ak_fetch(self.ak.index_stock_cons_csindex, symbol=index_code)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese field names to English."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            validated.append({
                "index_code": self._safe_str(row.get("指数代码")),
                "index_name": self._safe_str(row.get("指数名称")),
                "index_name_en": self._safe_str(row.get("指数英文名称")),
                "stock_code": self._safe_str(row.get("成分券代码")),
                "stock_name": self._safe_str(row.get("成分券名称")),
                "stock_name_en": self._safe_str(row.get("成分券英文名称")),
                "exchange": self._safe_str(row.get("交易所")),
                "exchange_en": self._safe_str(row.get("交易所英文名称")),
                "snapshot_date": self._safe_str(row.get("日期")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records, deduplicating by (index_code, stock_code, snapshot_date)."""
        return self._store_dedup(
            RawIndexCons, records, ["index_code", "stock_code", "snapshot_date"]
        )
