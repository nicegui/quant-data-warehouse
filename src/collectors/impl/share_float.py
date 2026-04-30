"""限售股解禁 — ShareFloatCollector

Tushare share_float API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.market import RawShareFloat
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ShareFloatCollector(BaseTushareCollector):
    """限售股解禁 collector."""

    def __init__(self, token: str):
        super().__init__("share_float", token)

    @property
    def checkpoint_key(self):
        return "float_date"

    def fetch(self, ts_code: str = "", ann_date: str = "", start_date: str = "",
              end_date: str = "", float_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        # float_date is the checkpoint key; API may not support it directly,
        # but we handle it via start_date/end_date
        if float_date:
            params["start_date"] = float_date
        return self.api_call("share_float", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "float_date": row.get("float_date"),
                "float_share": _f(row.get("float_share")),
                "float_ratio": _f(row.get("float_ratio")),
                "holder_name": row.get("holder_name"),
                "share_type": row.get("share_type"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawShareFloat).filter_by(
                    ts_code=rec["ts_code"],
                    float_date=rec.get("float_date"),
                    holder_name=rec.get("holder_name"),
                ).first()
                if existing:
                    continue
                session.add(RawShareFloat(**rec))
                written += 1
        return written
