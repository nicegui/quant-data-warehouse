"""融资融券明细 — MarginDetailCollector

Tushare margin_detail API — 个股两融交易日明细.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMarginDetail
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class MarginDetailCollector(BaseTushareCollector):
    """融资融券明细 collector."""

    def __init__(self, token: str):
        super().__init__("margin_detail", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("margin_detail", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "rzye": _f(row.get("rzye")),
                "rqye": _f(row.get("rqye")),
                "rzmre": _f(row.get("rzmre")),
                "rqyl": _f(row.get("rqyl")),
                "rzche": _f(row.get("rzche")),
                "rqchl": _f(row.get("rqchl")),
                "rqmcl": _f(row.get("rqmcl")),
                "rzrqye": _f(row.get("rzrqye")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMarginDetail).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawMarginDetail(**rec))
                written += 1
        return written
