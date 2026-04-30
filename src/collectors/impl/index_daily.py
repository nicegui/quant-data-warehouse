"""指数日线 — IndexCollector

index_daily + sw_daily from Tushare API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RawIndexDaily, RawSwDaily
from src.collectors.base import BaseTushareCollector


class IndexCollector(BaseTushareCollector):
    """指数日线 collector."""

    def __init__(self, token: str):
        super().__init__("index_daily", token)

    def fetch_index(self, trade_date: str) -> list[dict]:
        return self.api_call("index_daily", trade_date=trade_date)

    def store_index(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawIndexDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawIndexDaily(**rec))
                written += 1
        return written

    def fetch_sw_daily(self, trade_date: str) -> list[dict]:
        return self.api_call("sw_daily", trade_date=trade_date)

    def store_sw_daily(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawSwDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawSwDaily(**rec))
                written += 1
        return written
