"""可转债集思录 — CbJslCollector

Non-Tushare collector using akshare.bond_cb_jsl() for convertible bond Jisilu data.
Full pull (~30 records), dedup by code. No checkpoint (full refresh each run).
"""
from __future__ import annotations

import json
from typing import Any

from src.models.cb_jsl import RawCbJsl
from src.collectors.base import BaseAKShareCollector


class CbJslCollector(BaseAKShareCollector):
    """可转债集思录实时数据 collector via akshare (non-Tushare)."""

    def __init__(self):
        super().__init__("cb_jsl")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch 可转债集思录 data from akshare."""
        return self._ak_fetch(self.ak.bond_cb_jsl)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese field names to English."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            validated.append({
                "code": self._safe_str(row.get("代码")),
                "name": self._safe_str(row.get("转债名称")) or None,
                "price": self._safe_float(row.get("现价")),
                "pct_chg": self._safe_float(row.get("涨跌幅")),
                "stock_code": self._safe_str(row.get("正股代码")) or None,
                "stock_name": self._safe_str(row.get("正股名称")) or None,
                "stock_price": self._safe_float(row.get("正股价")),
                "stock_pct_chg": self._safe_float(row.get("正股涨跌")),
                "stock_pb": self._safe_float(row.get("正股PB")),
                "conv_price": self._safe_float(row.get("转股价")),
                "conv_value": self._safe_float(row.get("转股价值")),
                "conv_premium": self._safe_float(row.get("转股溢价率")),
                "bond_rating": self._safe_str(row.get("债券评级")) or None,
                "put_price": self._safe_float(row.get("回售触发价")),
                "call_price": self._safe_float(row.get("强赎触发价")),
                "cb_ratio": self._safe_float(row.get("转债占比")),
                "maturity_date": self._safe_str(row.get("到期时间")) or None,
                "remain_years": self._safe_float(row.get("剩余年限")),
                "remain_size": self._safe_float(row.get("剩余规模")),
                "volume": self._safe_float(row.get("成交额")),
                "turnover_rate": self._safe_float(row.get("换手率")),
                "ytm": self._safe_float(row.get("到期税前收益")),
                "dual_low": self._safe_float(row.get("双低")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records, deduplicating by code."""
        return self._store_dedup(RawCbJsl, records, ["code"])
