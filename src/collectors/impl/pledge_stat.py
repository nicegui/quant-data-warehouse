"""质押统计 — PledgeStatCollector

Tushare pledge_stat API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawPledgeStat
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class PledgeStatCollector(BaseTushareCollector):
    """质押统计 collector."""

    def __init__(self, token: str):
        super().__init__("pledge_stat", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("pledge_stat", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "pledge_count": row.get("pledge_count"),
                "unrest_pledge": _f(row.get("unrest_pledge")),
                "rest_pledge": _f(row.get("rest_pledge")),
                "total_share": _f(row.get("total_share")),
                "pledge_ratio": _f(row.get("pledge_ratio")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawPledgeStat).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec.get("end_date"),
                ).first()
                if existing:
                    continue
                session.add(RawPledgeStat(**rec))
                written += 1
        return written
