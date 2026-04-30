"""复权因子 — AdjFactorCollector

Forward adjustment factor collector for split/dividend adjustments.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.reference import RefAdjFactor
from src.collectors.base import BaseTushareCollector


class AdjFactorCollector(BaseTushareCollector):
    """Forward adjustment factor collector."""

    def __init__(self, token: str):
        super().__init__("adj_factor", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        params = {}
        start_date = kwargs.get("start_date", "20000101")
        trade_date = kwargs.get("trade_date")
        if trade_date:
            params["trade_date"] = trade_date
        else:
            params["start_date"] = start_date
        return self.api_call("adj_factor", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "adj_factor": float(row.get("adj_factor", 1)),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Upsert adj factors."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefAdjFactor).filter(
                    RefAdjFactor.ts_code == rec["ts_code"],
                    RefAdjFactor.trade_date == rec["trade_date"],
                ).first()
                if existing:
                    existing.adj_factor = rec["adj_factor"]
                else:
                    session.add(RefAdjFactor(**rec))
                written += 1
        return written
