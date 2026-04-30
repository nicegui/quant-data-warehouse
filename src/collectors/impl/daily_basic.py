"""每日基本面 — DailyBasicCollector

A-share daily basic indicators (PE/PB/换手率/市值).
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.market import RawDailyBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f
from sqlalchemy import and_


class DailyBasicCollector(BaseTushareCollector):
    """A-share daily basic indicators collector."""

    def __init__(self, token: str):
        super().__init__("daily_basic", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt

        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        else:
            params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("daily_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "close": _f(row.get("close")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "pre_close": _f(row.get("pre_close")) or 0,
                "change": _f(row.get("change")) or 0,
                "pct_chg": _f(row.get("pct_chg")) or 0,
                "vol": _f(row.get("vol")) or 0,
                "amount": _f(row.get("amount")) or 0,
                "turnover_rate": _f(row.get("turnover_rate")),
                "turnover_rate_f": _f(row.get("turnover_rate_f")),
                "pe": _f(row.get("pe")),
                "pe_ttm": _f(row.get("pe_ttm")),
                "pb": _f(row.get("pb")),
                "ps": _f(row.get("ps")),
                "ps_ttm": _f(row.get("ps_ttm")),
                "dv_ratio": _f(row.get("dv_ratio")),
                "dv_ttm": _f(row.get("dv_ttm")),
                "total_mv": _f(row.get("total_mv")),
                "circ_mv": _f(row.get("circ_mv")),
                "total_share": _f(row.get("total_share")),
                "float_share": _f(row.get("float_share")),
                "free_share": _f(row.get("free_share")),
                "avg_price": _f(row.get("avg_price")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawDailyBasic).filter(
                    and_(
                        RawDailyBasic.ts_code == rec["ts_code"],
                        RawDailyBasic.trade_date == rec["trade_date"],
                    )
                ).first()
                if existing:
                    continue
                session.add(RawDailyBasic(**rec))
                written += 1
        return written
