"""新股上市 — NewShareCollector

Tushare new_share API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.reference import RawNewShare
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class NewShareCollector(BaseTushareCollector):
    """新股上市 collector (全量拉取)."""

    def __init__(self, token: str):
        super().__init__("new_share", token)

    def fetch(self, start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("new_share", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "sub_code": row.get("sub_code", ""),
                "name": row.get("name", ""),
                "ipo_date": row.get("ipo_date"),
                "issue_date": row.get("issue_date"),
                "amount": _f(row.get("amount")),
                "market_amount": _f(row.get("market_amount")),
                "price": _f(row.get("price")),
                "pe": _f(row.get("pe")),
                "limit_amount": _f(row.get("limit_amount")),
                "funds": _f(row.get("funds")),
                "ballot": _f(row.get("ballot")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawNewShare).filter_by(
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawNewShare(**rec))
                written += 1
        return written
