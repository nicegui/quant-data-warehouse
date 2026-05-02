"""ST股票列表 — StockStCollector

Tushare stock_st API — 每日 ST/PT 股票列表，数据始于 2016-01-01。
支持 checkpoint 按 trade_date 增量更新。
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawStockSt
from src.collectors.base import BaseTushareCollector


class StockStCollector(BaseTushareCollector):
    """ST 股票列表 collector."""

    def __init__(self, token: str):
        super().__init__("stock_st", token)

    @property
    def checkpoint_key(self) -> str:
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("stock_st", **params)

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
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStockSt).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawStockSt(**rec))
                written += 1
        return written
