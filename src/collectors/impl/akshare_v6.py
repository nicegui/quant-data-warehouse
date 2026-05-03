"""IPO申报 — AkshareV6Collector."""

from __future__ import annotations
import json
from typing import Any
from src.models.akshare_v6 import RawIpoDeclare
from src.collectors.base import BaseAKShareCollector


class AkshareV6Collector(BaseAKShareCollector):
    """Batch 6: IPO申报."""

    def __init__(self):
        super().__init__("akshare_v6")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self._ak_fetch(self.ak.stock_ipo_declare_em)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "company_name": str(row.get("企业名称", "")),
                "status": str(row.get("最新状态", "")) if row.get("最新状态") else None,
                "location": str(row.get("注册地", "")) if row.get("注册地") else None,
                "underwriter": str(row.get("保荐机构", "")) if row.get("保荐机构") else None,
                "law_firm": str(row.get("律师事务所", "")) if row.get("律师事务所") else None,
                "accountant": str(row.get("会计师事务所", "")) if row.get("会计师事务所") else None,
                "market": str(row.get("拟上市地点", "")) if row.get("拟上市地点") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            if rec["company_name"]:
                validated.append(rec)
        return validated

    def store_raw(self, records: list) -> int:
        if not records: return 0
        return self._store_dedup(RawIpoDeclare, records, ["company_name"])
