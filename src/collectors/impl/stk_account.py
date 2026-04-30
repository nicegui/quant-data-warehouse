"""股票开户数 — StkAccountCollector

Tushare stk_account API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.market import RawStkAccount
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkAccountCollector(BaseTushareCollector):
    """股票开户数 collector."""

    def __init__(self, token: str):
        super().__init__("stk_account", token)

    @property
    def checkpoint_key(self):
        return "date"

    def fetch(self, date: str = "", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        """Fetch stock account opening statistics.

        Args:
            date: YYYYMM (single month, for checkpoint resume)
            start_date: YYYYMM
            end_date: YYYYMM
        """
        params: dict[str, Any] = {}
        if date:
            params["date"] = date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("stk_account", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "date": row.get("date"),
                "weekly_new": _f(row.get("weekly_new")),
                "total": _f(row.get("total")),
                "weekly_hold": _f(row.get("weekly_hold")),
                "weekly_trade": _f(row.get("weekly_trade")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkAccount).filter_by(
                    date=rec["date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkAccount(**rec))
                written += 1
        return written
