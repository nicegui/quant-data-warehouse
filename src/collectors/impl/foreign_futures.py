"""国际期货历史行情 — ForeignFuturesCollector

AKShare futures_foreign_hist collector.
Supports: CL(WTI), OIL(Brent), NG(NatGas), GC(Gold), SI(Silver), etc.
"""
from __future__ import annotations

import json
from typing import Any

from src.collectors.base import BaseAKShareCollector
from src.models.foreign_futures import RawForeignFutures


class ForeignFuturesCollector(BaseAKShareCollector):
    """国际期货日线 collector (Brent/WTI/黄金/天然气...)."""

    def __init__(self):
        super().__init__("foreign_futures")

    @property
    def checkpoint_key(self) -> str:
        return "date"

    def fetch(self, symbol: str = "CL", **kwargs) -> list[dict[str, Any]]:
        """Fetch foreign futures history.

        Args:
            symbol: contract code (CL=WTI, OIL=Brent, NG=NatGas, GC=Gold, SI=Silver)
        """
        rows = self._ak_fetch(self.ak.futures_foreign_hist, symbol=symbol)
        for row in rows:
            row["_symbol"] = symbol
        return rows

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated: list[dict[str, Any]] = []
        for row in raw:
            date_val = self._safe_str(row.get("date"))
            if " " in date_val:
                date_val = date_val.split(" ")[0]  # "2026-05-01 00:00:00" → "2026-05-01"
            validated.append({
                "symbol": self._safe_str(row.pop("_symbol", "")),
                "date": date_val,
                "open": self._safe_float(row.get("open")),
                "high": self._safe_float(row.get("high")),
                "low": self._safe_float(row.get("low")),
                "close": self._safe_float(row.get("close")),
                "volume": int(row.get("volume", 0)) if row.get("volume") else None,
                "position": int(row.get("position", 0)) if row.get("position") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawForeignFutures, records, ["symbol", "date"])
