"""指数日线 — IndexCollector

index_daily + sw_daily + index_weight from Tushare API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RawIndexDaily, RawSwDaily, RawIndexWeight
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class IndexCollector(BaseTushareCollector):
    """指数日线 collector."""

    def __init__(self, token: str):
        super().__init__("index_daily", token)

    # ── 指数日线 ──

    def fetch_index(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        params = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("index_daily", **params)

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

    # ── 申万行业指数 ──

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

    # ── 指数成分权重 ──

    def fetch_index_weight(self, index_code: str, trade_date: str) -> list[dict]:
        """Fetch constituent weights for a given index.

        Args:
            index_code: index code (e.g. '000300.SH', '000905.SH')
            trade_date: YYYYMMDD (monthly)
        """
        return self.api_call("index_weight", index_code=index_code, trade_date=trade_date)

    def store_index_weight(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawIndexWeight).filter_by(
                    index_code=rec["index_code"],
                    con_code=rec["con_code"],
                    trade_date=rec.get("trade_date"),
                ).first()
                if existing:
                    continue
                session.add(RawIndexWeight(**rec))
                written += 1
        return written
