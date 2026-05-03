"""中美收益率曲线 — AkshareV13Collector."""

from __future__ import annotations
import json
from typing import Any
import pandas as pd
from src.models.akshare_v10 import RawMacroIndicator
from src.collectors.base import BaseAKShareCollector


class AkshareV13Collector(BaseAKShareCollector):
    """Batch 13: 中美收益率曲线 (bond_zh_us_rate)."""

    def __init__(self):
        super().__init__("akshare_v13")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawMacroIndicator, records, ["source", "date", "sub_key"])

    def run(self, **kwargs) -> int:
        df = self.ak.bond_zh_us_rate()
        records = []

        # Map Chinese names to source keys
        col_map = {
            "中国国债收益率2年": ("cn_bond_2y", "value"),
            "中国国债收益率5年": ("cn_bond_5y", "value"),
            "中国国债收益率10年": ("cn_bond_10y", "value"),
            "中国国债收益率30年": ("cn_bond_30y", "value"),
            "中国国债收益率10年-2年": ("cn_bond_spread", "spread"),
            "中国GDP年增率": ("cn_gdp", "value"),
            "美国国债收益率2年": ("us_bond_2y", "value"),
            "美国国债收益率5年": ("us_bond_5y", "value"),
            "美国国债收益率10年": ("us_bond_10y", "value"),
            "美国国债收益率30年": ("us_bond_30y", "value"),
            "美国国债收益率10年-2年": ("us_bond_spread", "spread"),
            "美国GDP年增率": ("us_gdp", "value"),
        }

        for _, row in df.iterrows():
            date_str = str(row["日期"])[:10]
            for col, (src, metric_type) in col_map.items():
                v = row.get(col)
                if pd.isna(v):
                    continue
                records.append({
                    "source": src,
                    "date": date_str,
                    "sub_key": metric_type,
                    "value": float(v),
                    "change_pct": None,
                    "raw_json": json.dumps({"date": date_str, "metric": col, "value": float(v)}, ensure_ascii=False),
                })

        n = self.store_raw(records)
        print(f"bond_zh_us_rate: {n} rows ({len(df)} dates × {len(col_map)} metrics)")
        return n
