"""龙虎榜明细 — TopListCollector

Tushare top_list API.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawTopList
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class TopListCollector(BaseTushareCollector):
    """龙虎榜明细 collector."""

    def __init__(self, token: str):
        super().__init__("top_list", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("top_list", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name"),
                "reason": row.get("reason"),
                "close_price": _f(row.get("close")),
                "pct_chg": _f(row.get("pct_change")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "total_amount": _f(row.get("amount")),
                "net_amount": _f(row.get("net_amount")),
                "buy_amount": _f(row.get("buy_amount")),
                "sell_amount": _f(row.get("sell_amount")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawTopList).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawTopList(**rec))
                written += 1
        return written
