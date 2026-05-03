"""空气质量 — AkshareV12Collector."""

from __future__ import annotations
import json
from typing import Any
import pandas as pd
from src.models.akshare_v10 import RawMacroIndicator
from src.collectors.base import BaseAKShareCollector


class AkshareV12Collector(BaseAKShareCollector):
    """Batch 12: 空气质量 (河北)."""

    def __init__(self):
        super().__init__("akshare_v12")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawMacroIndicator, records, ["source", "date", "sub_key"])

    def run(self, **kwargs) -> int:
        total = 0
        try:
            df = self.ak.air_quality_hebei()
            records = []
            for _, row in df.iterrows():
                records.append({
                    "source": "air_hebei",
                    "date": str(row["时间"])[:16],
                    "sub_key": str(row.get("城市", "")) + "/" + str(row.get("监测点", "")),
                    "value": float(row["AQI"]) if not pd.isna(row.get("AQI")) else None,
                    "change_pct": None,
                    "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
                })
            n = self.store_raw(records)
            print(f"  河北空气质量: {n} rows")
            total += n
        except Exception as e:
            print(f"  河北空气质量: SKIP ({e})")
        return total
