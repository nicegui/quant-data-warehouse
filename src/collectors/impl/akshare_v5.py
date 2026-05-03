"""基金评级+基金经理+信用利差 — AkshareV5Collector."""

from __future__ import annotations
import json
from typing import Any
from src.models.akshare_v5 import RawFundRating, RawFundManager, RawCreditSpread
from src.collectors.base import BaseAKShareCollector


class AkshareV5Collector(BaseAKShareCollector):
    """Batch 5: 基金评级 + 基金经理 + 信用利差."""

    def __init__(self):
        super().__init__("akshare_v5")

    def fetch(self, sub_api: str = "fund_rating", **kwargs) -> list[dict[str, Any]]:
        if sub_api == "fund_rating":
            return self._ak_fetch(self.ak.fund_rating_all)
        elif sub_api == "fund_manager":
            return self._ak_fetch(self.ak.fund_manager_em)
        elif sub_api == "credit_spread":
            rows = self._ak_fetch(self.ak.bond_available_index_cbond)
            result = []
            for r in rows:
                result.append({"index": str(r.get("index", "")), "value": r.get("value")})
            return result
        raise ValueError(f"Unknown sub_api: {sub_api}")

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = self._norm(row)
            if rec:
                validated.append(rec)
        return validated

    def _norm(self, row: dict) -> dict | None:
        if "5星评级家数" in row:
            return {
                "fund_code": str(row.get("代码", "")),
                "fund_name": str(row.get("简称", "")) if row.get("简称") else None,
                "manager": str(row.get("基金经理", "")) if row.get("基金经理") else None,
                "company": str(row.get("基金公司", "")) if row.get("基金公司") else None,
                "rating_5star": self._si(row.get("5星评级家数")),
                "shanghai_rating": str(row.get("上海证券", "")) if row.get("上海证券") else None,
                "zhaoshang_rating": str(row.get("招商证券", "")) if row.get("招商证券") else None,
                "jian_rating": str(row.get("济安金信", "")) if row.get("济安金信") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        if "累计从业时间" in row:
            return {
                "name": str(row.get("姓名", "")),
                "company": str(row.get("所属公司", "")) if row.get("所属公司") else None,
                "fund_codes": str(row.get("现任基金代码", "")) if row.get("现任基金代码") else None,
                "fund_names": str(row.get("现任基金", "")) if row.get("现任基金") else None,
                "tenure": str(row.get("累计从业时间", "")) if row.get("累计从业时间") else None,
                "aum": str(row.get("现任基金资产总规模", "")) if row.get("现任基金资产总规模") else None,
                "best_return": str(row.get("现任基金最佳回报", "")) if row.get("现任基金最佳回报") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        if "index" in row:
            return {
                "index_name": str(row["index"]),
                "value": self._sf(row.get("value")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        return {"raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    @staticmethod
    def _sf(val):
        try: return float(val) if val not in (None, "") else None
        except: return None

    @staticmethod
    def _si(val):
        try: return int(float(val)) if val not in (None, "") else None
        except: return None

    def store_raw(self, records: list) -> int:
        if not records: return 0
        f = records[0]
        if "rating_5star" in f:
            return self._store_dedup(RawFundRating, records, ["fund_code"])
        if "tenure" in f:
            return self._store_dedup(RawFundManager, records, ["name", "company"])
        if "index_name" in f:
            return self._store_dedup(RawCreditSpread, records, ["index_name"])
        return 0
