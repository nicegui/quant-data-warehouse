"""股票更名 — NameChangeCollector

Tushare namechange API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.reference import RawNameChange
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class NameChangeCollector(BaseTushareCollector):
    """股票更名 collector."""

    def __init__(self, token: str):
        super().__init__("namechange", token)

    @property
    def checkpoint_key(self):
        return None  # 全量拉取，数据量小

    def fetch(self, ts_code: str = "", start_date: str = "", end_date: str = "",
              **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("namechange", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name", ""),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "ann_date": row.get("ann_date"),
                "change_reason": row.get("change_reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawNameChange).filter_by(
                    ts_code=rec["ts_code"],
                    start_date=rec.get("start_date"),
                ).first()
                if existing:
                    continue
                session.add(RawNameChange(**rec))
                written += 1
        return written
