"""财报披露计划 — DisclosureDateCollector

Tushare disclosure_date API — 财报预约披露日期.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.reference import RefDisclosureDate
from src.collectors.base import BaseTushareCollector


class DisclosureDateCollector(BaseTushareCollector):
    """财报披露计划 collector."""

    def __init__(self, token: str):
        super().__init__("disclosure_date", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", end_date: str = "",
              pre_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        if pre_date:
            params["pre_date"] = pre_date
        return self.api_call("disclosure_date", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "pre_date": row.get("pre_date"),
                "actual_date": row.get("actual_date"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefDisclosureDate).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                    end_date=rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RefDisclosureDate(**rec))
                written += 1
        return written
