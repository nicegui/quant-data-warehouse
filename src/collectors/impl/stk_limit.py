"""涨跌停价格限制 — StkLimitCollector

Tushare stk_limit API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawStkLimit
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkLimitCollector(BaseTushareCollector):
    """涨跌停价格限制 collector."""

    def __init__(self, token: str):
        super().__init__("stk_limit", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt

        td = trade_date or dt.now().strftime("%Y%m%d")
        return self.api_call("stk_limit", trade_date=td)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "pre_close": _f(row.get("pre_close")),
                "up_limit": _f(row.get("up_limit")),
                "down_limit": _f(row.get("down_limit")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkLimit).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkLimit(**rec))
                written += 1
        return written
