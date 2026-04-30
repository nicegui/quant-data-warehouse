"""财务指标 — FinancialIndicatorCollector

Financial indicators (ROE/EPS/PE/PB).
"""

from __future__ import annotations

import json
from typing import Any, Optional

from src.db.session import db_session
from src.models.fundamental import RawFinancialIndicators
from src.collectors.base import BaseTushareCollector


class FinancialIndicatorCollector(BaseTushareCollector):
    """Financial indicators collector."""

    def __init__(self, token: str):
        super().__init__("financial_indicators", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("fina_indicator_vip", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "eps": self._safe_float(row.get("eps")),
                "roe": self._safe_float(row.get("roe")),
                "bps": self._safe_float(row.get("bps")),
                "pe": self._safe_float(row.get("pe")),
                "pb": self._safe_float(row.get("pb")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialIndicators).filter(
                    RawFinancialIndicators.ts_code == rec["ts_code"],
                    RawFinancialIndicators.end_date == rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialIndicators(**rec))
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
