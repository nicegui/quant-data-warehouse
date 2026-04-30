"""复权因子 — AdjFactorCollector

Tushare adj_factor API.
"""

from __future__ import annotations

from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.reference import RefAdjFactor
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class AdjFactorCollector(BaseTushareCollector):
    """复权因子 collector."""

    def __init__(self, token: str):
        super().__init__("adj_factor", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("adj_factor", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "adj_factor": _f(row.get("adj_factor"), 1.0),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefAdjFactor).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RefAdjFactor(**rec))
                written += 1
        return written
