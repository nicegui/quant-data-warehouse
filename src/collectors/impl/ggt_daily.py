"""港股通日度成交统计 — GgtDailyCollector

Tushare ggt_daily API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawGgtDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class GgtDailyCollector(BaseTushareCollector):
    """港股通日度成交统计 collector."""

    def __init__(self, token: str):
        super().__init__("ggt_daily", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        """Fetch HK-SH/SZ Connect daily stats.

        Args:
            trade_date: YYYYMMDD (single date)
            start_date: YYYYMMDD (range start)
            end_date: YYYYMMDD (range end)
        """
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("ggt_daily", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "buy_amount": _f(row.get("buy_amount"), 0),
                "buy_volume": _f(row.get("buy_volume"), 0),
                "sell_amount": _f(row.get("sell_amount"), 0),
                "sell_volume": _f(row.get("sell_volume"), 0),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawGgtDaily).filter_by(
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawGgtDaily(**rec))
                written += 1
        return written
