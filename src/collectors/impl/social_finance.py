"""社融 collector — macro_china_new_financial_credit()."""
from __future__ import annotations
import json
from typing import Any
from src.collectors.base import BaseAKShareCollector
from src.models.macro_fund import RawSocialFinance


class SocialFinanceCollector(BaseAKShareCollector):
    """社融/新增信贷/货币供应."""

    def __init__(self):
        super().__init__("social_finance")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self._ak_fetch(self.ak.macro_china_new_financial_credit)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not raw:
            return []
        validated = []
        for row in raw:
            rec = {
                "month": self._safe_str(row.get("月份") or row.get("month")),
                "social_finance": self._safe_float(row.get("社会融资规模")),
                "new_loan": self._safe_float(row.get("新增人民币贷款")),
                "m2_yoy": self._safe_float(row.get("M2同比") or row.get("M2-同比增长")),
                "m1_yoy": self._safe_float(row.get("M1同比") or row.get("M1-同比增长")),
                "m0_yoy": self._safe_float(row.get("M0同比") or row.get("M0-同比增长")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawSocialFinance, records, ["month"])
