"""龙虎榜机构成交明细 — TopInstCollector

Tushare top_inst API.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from src.db.session import db_session
from src.models.sentiment import RawTopInst
from src.collectors.base import BaseTushareCollector


class TopInstCollector(BaseTushareCollector):
    """龙虎榜机构成交明细 collector."""

    def __init__(self, token: str):
        super().__init__("top_inst", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict[str, Any]]:
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        else:
            from datetime import datetime as dt

            params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("top_inst", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "exalter": row.get("exalter"),
                "buy": self._safe_float(row.get("buy")) or 0,
                "buy_rate": self._safe_float(row.get("buy_rate")),
                "sell": self._safe_float(row.get("sell")) or 0,
                "sell_rate": self._safe_float(row.get("sell_rate")),
                "net_buy": self._safe_float(row.get("net_buy")) or 0,
                "side": row.get("side"),
                "reason": row.get("reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawTopInst).filter(
                    RawTopInst.ts_code == rec["ts_code"],
                    RawTopInst.trade_date == rec["trade_date"],
                    RawTopInst.side == rec["side"],
                ).first()
                if existing:
                    continue
                session.add(RawTopInst(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
