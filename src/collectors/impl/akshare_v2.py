"""限售解禁+外汇黄金+消费+房地产 — AkshareV2Collector

Non-Tushare collector using akshare for 4 additional macro/event data sources.
Each sub_api has its own fetch/validate/store pathway.
"""

from __future__ import annotations

import json
from typing import Any

from src.models.akshare_v2 import (
    RawRestrictedRelease,
    RawFxGold,
    RawConsumerGoods,
    RawRealEstate,
)
from src.collectors.base import BaseAKShareCollector


class AkshareV2Collector(BaseAKShareCollector):
    """Batch 2 collector: 限售解禁 + 外汇黄金 + 消费 + 房地产."""

    def __init__(self):
        super().__init__("akshare_v2")

    def fetch(self, sub_api: str = "fx_gold", **kwargs) -> list[dict[str, Any]]:
        """Fetch data from akshare.

        Args:
            sub_api: one of "restricted_release", "fx_gold", "consumer_goods", "real_estate"
            **kwargs: forwarded to akshare function (e.g. start_date, end_date)
        """
        if sub_api == "restricted_release":
            start = kwargs.get("start_date", "20250101")
            end = kwargs.get("end_date", "20251231")
            return self._ak_fetch(
                self.ak.stock_restricted_release_detail_em,
                start_date=start, end_date=end,
            )
        elif sub_api == "fx_gold":
            return self._ak_fetch(self.ak.macro_china_fx_gold)
        elif sub_api == "consumer_goods":
            return self._ak_fetch(self.ak.macro_china_consumer_goods_retail)
        elif sub_api == "real_estate":
            return self._ak_fetch(self.ak.macro_china_real_estate)
        else:
            raise ValueError(f"Unknown sub_api: {sub_api}")

    # ── Validate ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = self._normalize(row)
            if rec:
                validated.append(rec)
        return validated

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any] | None:
        """Detect shape and normalize."""
        if "黄金储备-数值" in row:
            return self._normalize_fx_gold(row)
        if "限售股类型" in row or "解禁时间" in row:
            return self._normalize_restricted(row)
        if "累计" in row and "同比增长" in row:
            return self._normalize_consumer(row)
        if "近3月涨跌幅" in row:
            return self._normalize_real_estate(row)
        return {
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_restricted(self, row: dict) -> dict:
        return {
            "stock_code": str(row.get("股票代码", "")),
            "stock_name": str(row.get("股票简称", "")) if row.get("股票简称") else None,
            "release_date": str(row.get("解禁时间", "")),
            "release_type": str(row.get("限售股类型", "")) if row.get("限售股类型") else None,
            "planned_shares": self._safe_float(row.get("解禁数量")),
            "actual_shares": self._safe_float(row.get("实际解禁数量")),
            "actual_value": self._safe_float(row.get("实际解禁市值")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_fx_gold(self, row: dict) -> dict:
        return {
            "month": str(row.get("月份", "")),
            "gold_reserve": self._safe_float(row.get("黄金储备-数值")),
            "gold_yoy": self._safe_float(row.get("黄金储备-同比")),
            "gold_mom": self._safe_float(row.get("黄金储备-环比")),
            "fx_reserve": self._safe_float(row.get("国家外汇储备-数值")),
            "fx_yoy": self._safe_float(row.get("国家外汇储备-同比")),
            "fx_mom": self._safe_float(row.get("国家外汇储备-环比")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_consumer(self, row: dict) -> dict:
        return {
            "month": str(row.get("月份", "")),
            "value": self._safe_float(row.get("当月")),
            "yoy": self._safe_float(row.get("同比增长")),
            "mom": self._safe_float(row.get("环比增长")),
            "cumulative": self._safe_float(row.get("累计")),
            "cum_yoy": self._safe_float(row.get("累计-同比增长")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_real_estate(self, row: dict) -> dict:
        return {
            "date_str": str(row.get("日期", "")),
            "value": self._safe_float(row.get("最新值")),
            "change_pct": self._safe_float(row.get("涨跌幅")),
            "chg_3m": self._safe_float(row.get("近3月涨跌幅")),
            "chg_6m": self._safe_float(row.get("近6月涨跌幅")),
            "chg_1y": self._safe_float(row.get("近1年涨跌幅")),
            "chg_2y": self._safe_float(row.get("近2年涨跌幅")),
            "chg_3y": self._safe_float(row.get("近3年涨跌幅")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    # ── Store ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        first = records[0]
        if "gold_reserve" in first:
            return self._store_dedup(RawFxGold, records, ["month"])
        if "release_type" in first or "planned_shares" in first:
            return self._store_dedup(RawRestrictedRelease, records, ["stock_code", "release_date", "release_type"])
        if "cumulative" in first:
            return self._store_dedup(RawConsumerGoods, records, ["month"])
        if "chg_3m" in first:
            return self._store_dedup(RawRealEstate, records, ["date_str"])
        return 0
