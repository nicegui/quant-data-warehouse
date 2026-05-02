"""分析师排名 — AnalystCollector

AKShare collector for stock_analyst_rank_em(year=...).
Each year pulls ~100 analysts and replaces full-year snapshot on re-run.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.collectors.base import BaseAKShareCollector
from src.models.analyst import RawAnalystRank


class AnalystCollector(BaseAKShareCollector):
    """Analyst annual ranking via akshare stock_analyst_rank_em()."""

    def __init__(self):
        super().__init__("analyst_rank")

    # ── Fetch ──

    def fetch(self, year: str | None = None, **kwargs) -> list[dict[str, Any]]:
        """Fetch analyst rank for a given year.

        Args:
            year: year string, defaults to current year.
        """
        if year is None:
            year = str(datetime.now().year)
        return self._ak_fetch(self.ak.stock_analyst_rank_em, year=year)

    # ── Validate: Chinese → English field mapping ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese akshare columns to RawAnalystRank fields."""
        if not raw:
            return []

        # Detect the year-specific column: e.g. "2025年收益率"
        ret_annual_key = next(
            (k for k in raw[0].keys() if k.endswith("年收益率") and "最新" not in k), None
        )

        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = {
                "rank": self._safe_int(row.get("序号")),
                "name": self._safe_str(row.get("分析师名称")),
                "org": self._safe_str(row.get("分析师单位")),
                "year_index": self._safe_float(row.get("年度指数")),
                "ret_annual": self._safe_float(row.get(ret_annual_key)) if ret_annual_key else None,
                "ret_3m": self._safe_float(row.get("3个月收益率")),
                "ret_6m": self._safe_float(row.get("6个月收益率")),
                "ret_12m": self._safe_float(row.get("12个月收益率")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    # ── Store ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Dedup by (name, year_index); full replace per year on re-run."""
        if not records:
            return 0
        return self._store_dedup(RawAnalystRank, records, ["name", "year_index"])

    # ── Helpers ──

    @staticmethod
    def _safe_int(val: Any) -> int | None:
        """Coerce to int, return None on failure."""
        if val is None:
            return None
        try:
            return int(float(str(val)))
        except (ValueError, TypeError):
            return None
