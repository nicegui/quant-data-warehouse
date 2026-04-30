"""融资融券标的 — MarginSecsCollector

Tushare margin_secs API — 融资融券标的列表.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMarginSecs
from src.collectors.base import BaseTushareCollector


class MarginSecsCollector(BaseTushareCollector):
    """融资融券标的 collector (全量拉取)."""

    def __init__(self, token: str):
        super().__init__("margin_secs", token)

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("margin_secs", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date", ""),
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name", ""),
                "exchange": row.get("exchange", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMarginSecs).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawMarginSecs(**rec))
                written += 1
        return written
