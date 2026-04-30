"""宏观经济 — AkshareMacroCollector

Non-Tushare collector using akshare for CPI/PMI/GDP/MoneySupply data.
Each sub_api has its own fetch/validate/store pathway.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.akshare_macro import (
    RawAkshareCpi,
    RawAksharePmi,
    RawAkshareGdp,
    RawAkshareMoneySupply,
)
from src.collectors.base import BaseCollector


class AkshareMacroCollector(BaseCollector):
    """宏观经济 collector via akshare (non-Tushare)."""

    def __init__(self):
        super().__init__("akshare_macro")

    def fetch(self, sub_api: str = "cpi", **kwargs) -> list[dict[str, Any]]:
        """Fetch macro data from akshare.

        Args:
            sub_api: one of "cpi", "pmi", "gdp", "money_supply"
        """
        import akshare as ak

        if sub_api == "cpi":
            df = ak.macro_china_cpi_yearly()
        elif sub_api == "pmi":
            df = ak.macro_china_pmi()
        elif sub_api == "gdp":
            df = ak.macro_china_gdp()
        elif sub_api == "money_supply":
            df = ak.macro_china_money_supply()
        else:
            raise ValueError(f"Unknown sub_api: {sub_api}")

        if df is None or (hasattr(df, "empty") and df.empty):
            return []
        return df.to_dict(orient="records")

    # ── Validate: normalize Chinese field names to English ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize field names and coerce types. Delegates per shape."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = self._normalize(row)
            if rec:
                validated.append(rec)
        return validated

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any] | None:
        """Detect shape and normalize."""
        # CPI shape: has '日期', '今值', '预测值', '前值', '商品'
        if "今值" in row and "商品" in row:
            return self._normalize_cpi(row)
        # PMI shape: has '月份', '制造业-指数'
        if "制造业-指数" in row:
            return self._normalize_pmi(row)
        # GDP shape: has '季度', '国内生产总值-绝对值'
        if "国内生产总值-绝对值" in row:
            return self._normalize_gdp(row)
        # Money supply shape: has '货币和准货币(M2)-数量(亿元)'
        if "货币和准货币(M2)-数量(亿元)" in row:
            return self._normalize_money_supply(row)
        # Fallback: return as-is with raw_json
        return {
            "date_str": str(row.get("月份", row.get("日期", row.get("季度", "")))),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _safe_float(self, val: Any) -> float | None:
        """Try to coerce to float, return None on failure."""
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _normalize_cpi(self, row: dict) -> dict:
        return {
            "date_str": str(row.get("日期", "")),
            "item": str(row.get("商品", "")) if row.get("商品") else None,
            "value": self._safe_float(row.get("今值")),
            "forecast": self._safe_float(row.get("预测值")),
            "previous": self._safe_float(row.get("前值")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_pmi(self, row: dict) -> dict:
        return {
            "date_str": str(row.get("月份", "")),
            "mfg_index": self._safe_float(row.get("制造业-指数")),
            "mfg_yoy": self._safe_float(row.get("制造业-同比增长")),
            "non_mfg_index": self._safe_float(row.get("非制造业-指数")),
            "non_mfg_yoy": self._safe_float(row.get("非制造业-同比增长")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_gdp(self, row: dict) -> dict:
        return {
            "date_str": str(row.get("季度", "")),
            "gdp_abs": self._safe_float(row.get("国内生产总值-绝对值")),
            "gdp_yoy": self._safe_float(row.get("国内生产总值-同比增长")),
            "pi_abs": self._safe_float(row.get("第一产业-绝对值")),
            "pi_yoy": self._safe_float(row.get("第一产业-同比增长")),
            "si_abs": self._safe_float(row.get("第二产业-绝对值")),
            "si_yoy": self._safe_float(row.get("第二产业-同比增长")),
            "ti_abs": self._safe_float(row.get("第三产业-绝对值")),
            "ti_yoy": self._safe_float(row.get("第三产业-同比增长")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    def _normalize_money_supply(self, row: dict) -> dict:
        return {
            "date_str": str(row.get("月份", "")),
            "m2_qty": self._safe_float(row.get("货币和准货币(M2)-数量(亿元)")),
            "m2_yoy": self._safe_float(row.get("货币和准货币(M2)-同比增长")),
            "m2_mom": self._safe_float(row.get("货币和准货币(M2)-环比增长")),
            "m1_qty": self._safe_float(row.get("货币(M1)-数量(亿元)")),
            "m1_yoy": self._safe_float(row.get("货币(M1)-同比增长")),
            "m1_mom": self._safe_float(row.get("货币(M1)-环比增长")),
            "m0_qty": self._safe_float(row.get("流通中的现金(M0)-数量(亿元)")),
            "m0_yoy": self._safe_float(row.get("流通中的现金(M0)-同比增长")),
            "m0_mom": self._safe_float(row.get("流通中的现金(M0)-环比增长")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    # ── Store: route to correct table ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records into the correct raw table, deduplicating."""
        if not records:
            return 0

        # Detect which model to use by examining the first record's keys
        first = records[0]
        if "item" in first:
            return self._store(RawAkshareCpi, records, dedup_keys=["date_str", "item"])
        if "mfg_index" in first:
            return self._store(RawAksharePmi, records, dedup_keys=["date_str"])
        if "gdp_abs" in first:
            return self._store(RawAkshareGdp, records, dedup_keys=["date_str"])
        if "m2_qty" in first:
            return self._store(RawAkshareMoneySupply, records, dedup_keys=["date_str"])
        return 0

    def _store(self, model_cls, records: list[dict], dedup_keys: list[str]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                # Build filter from dedup keys
                filters = {k: rec[k] for k in dedup_keys if k in rec}
                if not filters:
                    continue
                existing = session.query(model_cls).filter_by(**filters).first()
                if existing:
                    continue
                session.add(model_cls(**rec))
                written += 1
        return written
