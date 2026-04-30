"""股东增减持 — StkHolderTradeCollector

Tushare stk_holdertrade API — 董监高持股变动.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawStkHolderTrade
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkHolderTradeCollector(BaseTushareCollector):
    """股东增减持 collector."""

    def __init__(self, token: str):
        super().__init__("stk_holdertrade", token)

    @property
    def checkpoint_key(self):
        return "ann_date"

    def fetch(self, ts_code: str = "", ann_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("stk_holdertrade", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "holder_name": row.get("holder_name", ""),
                "holder_type": row.get("holder_type"),
                "in_de": row.get("in_de"),
                "change_vol": _f(row.get("change_vol")),
                "change_ratio": _f(row.get("change_ratio")),
                "after_share": _f(row.get("after_share")),
                "after_ratio": _f(row.get("after_ratio")),
                "avg_price": _f(row.get("avg_price")),
                "total_share": _f(row.get("total_share")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkHolderTrade).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                    holder_name=rec["holder_name"],
                ).first()
                if existing:
                    continue
                session.add(RawStkHolderTrade(**rec))
                written += 1
        return written
