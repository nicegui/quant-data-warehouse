"""股权质押明细 — PledgeDetailCollector

Tushare pledge_detail API — 股东股权质押明细.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawPledgeDetail
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class PledgeDetailCollector(BaseTushareCollector):
    """股权质押明细 collector."""

    def __init__(self, token: str):
        super().__init__("pledge_detail", token)

    @property
    def checkpoint_key(self):
        return "ann_date"

    def fetch(self, ts_code: str = "", start_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("pledge_detail", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "holder_name": row.get("holder_name", ""),
                "pledge_amount": _f(row.get("pledge_amount")),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "is_release": row.get("is_release"),
                "release_date": row.get("release_date"),
                "pledgor": row.get("pledgor"),
                "holding_amount": _f(row.get("holding_amount")),
                "pledged_amount": _f(row.get("pledged_amount")),
                "p_total_ratio": _f(row.get("p_total_ratio")),
                "h_total_ratio": _f(row.get("h_total_ratio")),
                "is_buyback": row.get("is_buyback"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawPledgeDetail).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                    holder_name=rec["holder_name"],
                ).first()
                if existing:
                    continue
                session.add(RawPledgeDetail(**rec))
                written += 1
        return written
