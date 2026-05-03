"""QVIX 恐慌指数 + EPU 不确定性指数 collector."""
from __future__ import annotations
import json
from typing import Any
from src.collectors.base import BaseAKShareCollector
from src.models.qvix import RawQvix, RawEpuIndex


class QvixCollector(BaseAKShareCollector):
    """QVIX 期权恐慌指数 + EPU 不确定性指数."""

    def __init__(self):
        super().__init__("qvix")

    def fetch(self, underlying: str = "50ETF", **kwargs) -> list[dict[str, Any]]:
        if underlying == "300ETF":
            return self._ak_fetch(self.ak.index_option_300etf_qvix)
        return self._ak_fetch(self.ak.index_option_50etf_qvix)

    def validate(self, raw: list[dict[str, Any]], underlying: str = "50ETF") -> list[dict[str, Any]]:
        if not raw:
            return []
        validated = []
        for row in raw:
            rec = {
                "trade_date": self._safe_str(row.get("date") or row.get("日期")),
                "underlying": underlying,
                "open": self._safe_float(row.get("open")),
                "high": self._safe_float(row.get("high")),
                "low": self._safe_float(row.get("low")),
                "close": self._safe_float(row.get("close") or row.get("qvix")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawQvix, records, ["trade_date", "underlying"])

    def run_qvix(self) -> int:
        written = 0
        for und in ["50ETF", "300ETF"]:
            raw = self.fetch(underlying=und)
            valid = self.validate(raw, underlying=und)
            w = self.store_raw(valid)
            print(f"[qvix] {und}: {w} records")
            written += w
        return written


class EpuCollector(BaseAKShareCollector):
    """EPU 经济政策不确定性指数."""

    def __init__(self):
        super().__init__("epu_index")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self._ak_fetch(self.ak.article_epu_index)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize to RawEpuIndex."""
        if not raw:
            return []
        validated = []
        for row in raw:
            month_str = f"{self._safe_str(row.get('year'))}-{self._safe_str(row.get('month')).zfill(2)}"
            val = row.get("China_Policy_Index")
            if val is not None:
                validated.append({
                    "month": month_str,
                    "country": "China",
                    "epu_value": self._safe_float(val),
                    "raw_json": json.dumps(row, ensure_ascii=False, default=str),
                })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawEpuIndex, records, ["month", "country"])
