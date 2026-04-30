"""财务报告 — FinancialReportCollector

Financial reports via fina_mainbz_vip.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from src.db.session import db_session
from src.models.fundamental import RawFinancialReports
from src.collectors.base import BaseTushareCollector


class FinancialReportCollector(BaseTushareCollector):
    """Financial reports collector."""

    def __init__(self, token: str):
        super().__init__("financial_reports", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("fina_mainbz_vip", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "revenue": self._safe_float(row.get("revenue")),
                "operating_profit": self._safe_float(row.get("operating_profit")),
                "net_profit": self._safe_float(row.get("net_profit")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialReports).filter(
                    RawFinancialReports.ts_code == rec["ts_code"],
                    RawFinancialReports.end_date == rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialReports(**rec))
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
