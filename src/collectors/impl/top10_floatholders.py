"""十大流通股东 — Top10FloatHoldersCollector

Tushare top10_floatholders API — 前十大流通股东明细.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawStkHolderFloatTop
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class Top10FloatHoldersCollector(BaseTushareCollector):
    """十大流通股东 collector."""

    def __init__(self, token: str):
        super().__init__("top10_floatholders", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", ann_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("top10_floatholders", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "holder_name": row.get("holder_name", ""),
                "hold_amount": _f(row.get("hold_amount")),
                "hold_ratio": _f(row.get("hold_ratio")),
                "hold_float_ratio": _f(row.get("hold_float_ratio")),
                "hold_change": _f(row.get("hold_change")),
                "holder_type": row.get("holder_type"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkHolderFloatTop).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                    end_date=rec["end_date"],
                    holder_name=rec["holder_name"],
                ).first()
                if existing:
                    continue
                session.add(RawStkHolderFloatTop(**rec))
                written += 1
        return written
