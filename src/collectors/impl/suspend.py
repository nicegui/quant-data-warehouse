"""停复牌全量 — SuspendCollector

Tushare suspend API — 历史停复牌记录.
区别于 suspend_d（每日快照），这个是一次性全量数据.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.corporate_action import RawSuspend
from src.collectors.base import BaseTushareCollector


class SuspendCollector(BaseTushareCollector):
    """停复牌(全量) collector — 全量更新."""

    def __init__(self, token: str):
        super().__init__("suspend", token)

    def fetch(self, ts_code: str = "", suspend_type: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if suspend_type:
            params["suspend_type"] = suspend_type
        return self.api_call("suspend", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "suspend_date": row.get("suspend_date"),
                "resume_date": row.get("resume_date"),
                "suspend_reason": row.get("suspend_reason", ""),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawSuspend).filter_by(
                    ts_code=rec["ts_code"],
                    suspend_date=rec["suspend_date"],
                ).first()
                if existing:
                    continue
                session.add(RawSuspend(**rec))
                written += 1
        return written
