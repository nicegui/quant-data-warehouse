"""融资融券 — MarginCollector

Tushare margin API — 融资融券交易明细 (margin_detail).
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMarginDetail
from src.collectors.base import BaseTushareCollector


class MarginCollector(BaseTushareCollector):
    """融资融券明细 collector."""

    def __init__(self, token: str):
        super().__init__("margin", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", start_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {
            "fields": "trade_date,ts_code,name,rzye,rzmre,rzche,rqye,rqmcl,rzrqye",
        }
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("margin_detail", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name", ""),
                "rzye": row.get("rzye"),
                "rzmre": row.get("rzmre"),
                "rzche": row.get("rzche"),
                "rqye": row.get("rqye"),
                "rqmcl": row.get("rqmcl"),
                "rzrqye": row.get("rzrqye"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMarginDetail).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawMarginDetail(**rec))
                written += 1
        return written
