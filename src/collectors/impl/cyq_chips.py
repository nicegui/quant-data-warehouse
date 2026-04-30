"""筹码分布 — CyqChipsCollector

Tushare cyq_chips API — 全市场筹码分布数据.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawCyqChips
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CyqChipsCollector(BaseTushareCollector):
    """筹码分布 collector."""

    def __init__(self, token: str):
        super().__init__("cyq_chips", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", trade_date: str = "", **kwargs) -> list[dict]:
        """Fetch chip distribution data.

        Args:
            ts_code: Stock code (e.g. '000001.SZ')
            trade_date: Trade date YYYYMMDD (defaults to yesterday)
        """
        params: dict[str, Any] = {}
        if not ts_code and not trade_date:
            params["trade_date"] = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        params.update({k: v for k, v in kwargs.items() if v})
        return self.api_call("cyq_chips", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "price": _f(row.get("price"), default=0.0) or 0.0,
                "percent": _f(row.get("percent"), default=0.0) or 0.0,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCyqChips).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                    price=rec["price"],
                ).first()
                if existing:
                    continue
                session.add(RawCyqChips(**rec))
                written += 1
        return written
