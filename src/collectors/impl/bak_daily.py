"""备用行情 — BakDailyCollector

Tushare bak_daily API — 全市场日度备用行情数据（31字段）。
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.market import RawBakDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class BakDailyCollector(BaseTushareCollector):
    """备用行情 collector."""

    def __init__(self, token: str):
        super().__init__("bak_daily", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("bak_daily", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "name": row.get("name", ""),
                "pct_change": _f(row.get("pct_change")),
                "close": _f(row.get("close")),
                "change": _f(row.get("change")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "pre_close": _f(row.get("pre_close")),
                "vol_ratio": _f(row.get("vol_ratio")),
                "turn_over": _f(row.get("turn_over")),
                "swing": _f(row.get("swing")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "selling": _f(row.get("selling")),
                "buying": _f(row.get("buying")),
                "total_share": _f(row.get("total_share")),
                "float_share": _f(row.get("float_share")),
                "pe": _f(row.get("pe")),
                "industry": row.get("industry", ""),
                "area": row.get("area", ""),
                "float_mv": _f(row.get("float_mv")),
                "total_mv": _f(row.get("total_mv")),
                "avg_price": _f(row.get("avg_price")),
                "strength": _f(row.get("strength")),
                "activity": _f(row.get("activity")),
                "avg_turnover": _f(row.get("avg_turnover")),
                "attack": _f(row.get("attack")),
                "interval_3": row.get("interval_3", ""),
                "interval_6": row.get("interval_6", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawBakDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawBakDaily(**rec))
                written += 1
        return written
