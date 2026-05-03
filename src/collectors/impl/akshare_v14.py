"""社交情绪 — AkshareV14Collector.

雪球: 热门交易/关注/讨论 (hot_deal/hot_follow/hot_tweet)
微博: 情绪报告 (weibo_report)
"""

from __future__ import annotations
import json
from typing import Any
import pandas as pd
from src.models.akshare_v10 import RawMacroIndicator
from src.collectors.base import BaseAKShareCollector


class AkshareV14Collector(BaseAKShareCollector):
    """Batch 14: 雪球 + 微博情绪."""

    def __init__(self):
        super().__init__("akshare_v14")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawMacroIndicator, records, ["source", "date", "sub_key"])

    def _fetch_xq(self, api_func, source: str) -> list[dict]:
        df = api_func(symbol="最热门")
        records = []
        for _, row in df.iterrows():
            code = str(row.get("股票代码", ""))
            attention = row.get("关注")
            if pd.isna(attention):
                continue
            records.append({
                "source": source,
                "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "sub_key": code,
                "value": float(attention),
                "change_pct": None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    def _fetch_weibo(self) -> list[dict]:
        df = self.ak.stock_js_weibo_report(time_period="CNHOUR12")
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "weibo_report",
                "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "sub_key": str(row.get("name", "")),
                "value": float(row.get("rate", 0)) if not pd.isna(row.get("rate")) else None,
                "change_pct": None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    def run(self, **kwargs) -> int:
        total = 0
        fetchers = [
            ("雪球-交易热度", lambda: self._fetch_xq(self.ak.stock_hot_deal_xq, "xq_hot_deal")),
            ("雪球-关注数",   lambda: self._fetch_xq(self.ak.stock_hot_follow_xq, "xq_hot_follow")),
            ("雪球-讨论数",   lambda: self._fetch_xq(self.ak.stock_hot_tweet_xq, "xq_hot_tweet")),
            ("微博-情绪报告",  self._fetch_weibo),
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
