"""每日停复牌 — SuspendDCollector

Tushare suspend_d API.
"""

from __future__ import annotations

from typing import Any
from datetime import datetime as dt

from src.db.session import db_session
from src.models.corporate_action import RawSuspendD
from src.collectors.base import BaseTushareCollector


class SuspendDCollector(BaseTushareCollector):
    """每日停复牌 collector."""

    def __init__(self, token: str):
        super().__init__("suspend_d", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("suspend_d", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "suspend_timing": row.get("suspend_timing"),
                "suspend_type": row.get("suspend_type"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawSuspendD).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawSuspendD(**rec))
                written += 1
        return written
