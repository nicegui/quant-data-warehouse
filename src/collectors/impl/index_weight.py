"""指数成分权重 — IndexWeightCollector

Tushare index_weight API — 月度权重数据.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RawIndexWeight
from src.collectors.base import BaseTushareCollector


class IndexWeightCollector(BaseTushareCollector):
    """指数成分权重 collector."""

    def __init__(self, token: str):
        super().__init__("index_weight", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, index_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (index_code or trade_date):
            index_code = "000300.SH"
        if index_code:
            params["index_code"] = index_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("index_weight", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "index_code": row.get("index_code", ""),
                "con_code": row.get("con_code", ""),
                "trade_date": row.get("trade_date"),
                "weight": row.get("weight"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawIndexWeight).filter_by(
                    index_code=rec["index_code"],
                    con_code=rec["con_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawIndexWeight(**rec))
                written += 1
        return written
