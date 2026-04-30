"""交易日历 — TradeCalCollector

Tushare trade_cal API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.reference import RefTradeCal
from src.collectors.base import BaseTushareCollector


class TradeCalCollector(BaseTushareCollector):
    """交易日历 collector."""

    def __init__(self, token: str):
        super().__init__("trade_cal", token)

    def fetch(self, exchange: str = "SSE", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        """Fetch trade calendar.

        Args:
            exchange: SSE | SZSE | CFFEX | SHFE | CZCE | DCE
            start_date: YYYYMMDD
            end_date: YYYYMMDD
        """
        params = {"exchange": exchange, "is_open": ""}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("trade_cal", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            is_open = str(row.get("is_open", "0")).strip()
            validated.append({
                "exchange": row.get("exchange", ""),
                "cal_date": row.get("cal_date"),
                "is_open": is_open == "1",
                "pretrade_date": row.get("pretrade_date"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefTradeCal).filter_by(
                    exchange=rec["exchange"],
                    cal_date=rec["cal_date"],
                ).first()
                if existing:
                    existing.is_open = rec["is_open"]  # upsert
                    session.add(existing)
                else:
                    session.add(RefTradeCal(**rec))
                written += 1
        return written
