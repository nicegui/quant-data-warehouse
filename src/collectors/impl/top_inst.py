"""龙虎榜机构成交 — TopInstCollector

Tushare top_inst API.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawTopInst
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class TopInstCollector(BaseTushareCollector):
    """龙虎榜机构成交明细 collector."""

    def __init__(self, token: str):
        super().__init__("top_inst", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("top_inst", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "exalter": row.get("exalter"),
                "buy": _f(row.get("buy"), 0),
                "buy_rate": _f(row.get("buy_rate")),
                "sell": _f(row.get("sell"), 0),
                "sell_rate": _f(row.get("sell_rate")),
                "net_buy": _f(row.get("net_buy"), 0),
                "side": row.get("side"),
                "reason": row.get("reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawTopInst).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                    exalter=rec["exalter"],
                ).first()
                if existing:
                    continue
                session.add(RawTopInst(**rec))
                written += 1
        return written
