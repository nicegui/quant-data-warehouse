"""财务指标 — FinancialIndicatorCollector

Tushare fina_indicator API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawFinancialIndicators
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FinancialIndicatorCollector(BaseTushareCollector):
    """财务指标 collector."""

    def __init__(self, token: str):
        super().__init__("financial_indicators", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, end_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        params = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fina_indicator", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "eps": _f(row.get("eps")),
                "dt_eps": _f(row.get("dt_eps")),
                "bps": _f(row.get("bps")),
                "roe": _f(row.get("roe")),
                "roe_waa": _f(row.get("roe_waa")),
                "roa": _f(row.get("roa")),
                "npta": _f(row.get("npta")),
                "grossprofit_margin": _f(row.get("grossprofit_margin")),
                "netprofit_margin": _f(row.get("netprofit_margin")),
                "debt_to_assets": _f(row.get("debt_to_assets")),
                "pe": _f(row.get("pe")),
                "pb": _f(row.get("pb")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialIndicators).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialIndicators(**rec))
                written += 1
        return written
