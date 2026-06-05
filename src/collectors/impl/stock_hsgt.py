"""沪深港通股票列表 — StockHsgtCollector

Tushare stock_hsgt API — 日度沪深港通成分股快照。
数据始于 2025-08-12，type 参数必填，本 collector 自动遍历 4 种类型。
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawStockHsgt
from src.collectors.base import BaseTushareCollector

HSGT_TYPES = ("HK_SZ", "SZ_HK", "HK_SH", "SH_HK")


class StockHsgtCollector(BaseTushareCollector):
    """沪深港通股票列表 collector (4 类自动遍历)."""

    def __init__(self, token: str):
        super().__init__("stock_hsgt", token)

    @property
    def checkpoint_key(self) -> str:
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        """遍历 4 种类型，合并返回."""
        results: list[dict] = []
        for tp in HSGT_TYPES:
            rows = self.api_call("stock_hsgt", trade_date=trade_date, type=tp)
            results.extend(rows)
        return results

    def validate(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name", ""),
                "trade_date": row.get("trade_date"),
                "type": row.get("type"),
                "type_name": row.get("type_name"),
            }
            for row in raw
        ]
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStockHsgt, records, ["trade_date", "ts_code", "type"])
