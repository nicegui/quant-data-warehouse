"""上市公司基础信息 — StockCompanyCollector

Tushare stock_company API — 公司治理/简介，按交易所分批提取。
全量拉取，upsert 按 ts_code。
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.reference import RefStockCompany
from src.collectors.base import BaseTushareCollector


class StockCompanyCollector(BaseTushareCollector):
    """上市公司基础信息 collector (全量拉取)."""

    EXCHANGES = ("SSE", "SZSE", "BSE")

    def __init__(self, token: str):
        super().__init__("stock_company", token)

    def fetch(self, **kwargs) -> list[dict]:
        """遍历三大交易所，合并返回."""
        results: list[dict] = []
        for ex in self.EXCHANGES:
            rows = self.api_call("stock_company", exchange=ex, **kwargs)
            results.extend(rows)
        return results

    def validate(self, raw: list[dict]) -> list[dict]:
        import math
        fields = [
            "ts_code", "com_name", "com_id", "exchange",
            "chairman", "manager", "secretary", "reg_capital",
            "setup_date", "province", "city",
            "introduction", "website", "email", "office",
            "employees", "main_business", "business_scope",
        ]
        result = []
        for row in raw:
            rec = {}
            for f in fields:
                v = row.get(f)
                if isinstance(v, float) and math.isnan(v):
                    v = None
                rec[f] = v
            result.append(rec)
        return result

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefStockCompany).filter_by(
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    # Update existing
                    for k, v in rec.items():
                        if v is not None and k != "ts_code":
                            setattr(existing, k, v)
                else:
                    session.add(RefStockCompany(**rec))
                written += 1
        return written
