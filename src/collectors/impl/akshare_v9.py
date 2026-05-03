"""商品/物流/糖指数 — AkshareV9Collector."""

from __future__ import annotations
import json
from typing import Any
import pandas as pd
from src.models.akshare_v9 import RawCommodityLogistics
from src.collectors.base import BaseAKShareCollector


class AkshareV9Collector(BaseAKShareCollector):
    """Batch 9: 商品/物流/糖指数 (6 个数据源)."""

    def __init__(self):
        super().__init__("akshare_v9")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    # ── freight: macro_china_freight_index ──
    def _fetch_freight(self) -> list[dict]:
        df = self.ak.macro_china_freight_index()
        records = []
        for _, row in df.iterrows():
            for col in df.columns:
                if col == "截止日期":
                    continue
                v = row[col]
                if pd.isna(v):
                    continue
                records.append({
                    "source": "freight", "sub_index": col,
                    "date": str(row["截止日期"])[:10], "value": float(v),
                    "change_pct": None,
                    "raw_json": json.dumps({"date": str(row["截止日期"]), "index": col, "value": float(v)}, ensure_ascii=False),
                })
        return records

    # ── outer sugar ──
    def _fetch_outer_sugar(self) -> list[dict]:
        df = self.ak.index_outer_quote_sugar_msweet()
        records = []
        for _, row in df.iterrows():
            for col in df.columns:
                if col == "日期":
                    continue
                v = row[col]
                if pd.isna(v):
                    continue
                records.append({
                    "source": "sugar", "sub_index": f"配额外_{col}",
                    "date": str(row["日期"])[:10], "value": float(v),
                    "change_pct": None,
                    "raw_json": json.dumps({"date": str(row["日期"]), "index": col, "value": float(v)}, ensure_ascii=False),
                })
        return records

    # ── sugar msweet (raw API, AKShare has dtype bug) ──
    def _fetch_sugar_msweet(self) -> list[dict]:
        import requests
        r = requests.get("https://www.msweet.com.cn/eportal/ui", params={
            "struts.portlet.action": "/portlet/price!getSTZSJson.action",
            "moduleId": "cb752447cfe24b44b18c7a7e9abab048",
        }, timeout=15)
        data = r.json()
        records = []
        dates = data.get("category", [])
        series = data.get("data", {})
        for name, values in series.items():
            for i, v in enumerate(values):
                if v is None or v == "":
                    continue
                try:
                    fv = float(v)
                except (ValueError, TypeError):
                    continue
                date_str = str(dates[i])[:10] if i < len(dates) else ""
                records.append({
                    "source": "sugar", "sub_index": f"食糖_{name}",
                    "date": date_str,
                    "value": fv,
                    "change_pct": None,
                    "raw_json": json.dumps({"date": date_str, "index": name, "value": fv}, ensure_ascii=False),
                })
        return records

    # ── inner sugar (raw API) ──
    def _fetch_inner_sugar(self) -> list[dict]:
        import requests
        r = requests.get("https://www.msweet.com.cn/datacenterapply/datacenter/json/JinKongTang.json", timeout=15)
        data = r.json()
        records = []
        dates = data.get("category", [])
        series = data.get("data", {})
        for name, values in series.items():
            for i, v in enumerate(values):
                if v is None or v == "" or (isinstance(v, str) and v.startswith("=")):
                    continue
                try:
                    fv = float(v)
                except (ValueError, TypeError):
                    continue
                date_str = str(dates[i])[:10] if i < len(dates) else ""
                records.append({
                    "source": "sugar", "sub_index": f"配额内_{name}",
                    "date": date_str,
                    "value": fv,
                    "change_pct": None,
                    "raw_json": json.dumps({"date": date_str, "index": name, "value": fv}, ensure_ascii=False),
                })
        return records

    # ── cflp price / volume ──
    def _fetch_cflp(self, api_func, source_name: str, prefix: str) -> list[dict]:
        df = api_func()
        records = []
        for _, row in df.iterrows():
            for col in df.columns:
                if col == "日期":
                    continue
                v = row[col]
                if pd.isna(v):
                    continue
                records.append({
                    "source": source_name, "sub_index": f"{prefix}_{col}",
                    "date": str(row["日期"])[:10], "value": float(v),
                    "change_pct": None,
                    "raw_json": json.dumps({"date": str(row["日期"]), "index": col, "value": float(v)}, ensure_ascii=False),
                })
        return records

    # ── orchestrate ──
    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawCommodityLogistics, records, ["source", "sub_index", "date"])

    def run(self, **kwargs) -> int:
        total = 0
        fetchers = [
            ("freight",      self._fetch_freight),
            ("outer_sugar",  self._fetch_outer_sugar),
            ("sugar_msweet", self._fetch_sugar_msweet),
            ("inner_sugar",  self._fetch_inner_sugar),
            ("price_cflp",   lambda: self._fetch_cflp(self.ak.index_price_cflp, "price_cflp", "运价")),
            ("volume_cflp",  lambda: self._fetch_cflp(self.ak.index_volume_cflp, "volume_cflp", "运量")),
        ]
        for name, fetcher in fetchers:
            try:
                records = fetcher()
                n = self.store_raw(records)
                print(f"  {name}: {n} rows")
                total += n
            except Exception as e:
                print(f"  {name}: SKIP ({e})")
        print(f"\nTotal: {total} rows")
        return total
