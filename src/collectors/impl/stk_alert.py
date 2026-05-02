"""交易所重点提示证券 — StkAlertCollector

Tushare stk_alert API — 交易所每日发布的重点提示证券。
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawStkAlert
from src.collectors.base import BaseTushareCollector


class StkAlertCollector(BaseTushareCollector):
    """交易所重点提示证券 collector."""

    def __init__(self, token: str):
        super().__init__("stk_alert", token)

    @property
    def checkpoint_key(self):
        return "start_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if not (start_date or end_date):
            if trade_date:
                params["trade_date"] = trade_date
            elif not params:
                params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("stk_alert", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name"),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "type": row.get("type"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkAlert).filter_by(
                    ts_code=rec["ts_code"],
                    start_date=rec["start_date"],
                    end_date=rec.get("end_date"),
                ).first()
                if existing:
                    continue
                session.add(RawStkAlert(**rec))
                written += 1
        return written
