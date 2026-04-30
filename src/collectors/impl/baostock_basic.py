"""股票基本信息 — BaostockBasicCollector

Non-Tushare collector using baostock.query_stock_basic().
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from src.db.session import db_session
from src.models.baostock import RefBaostockBasic
from src.collectors.base import BaseCollector


class BaostockBasicCollector(BaseCollector):
    """股票基本信息 collector via baostock (non-Tushare)."""

    def __init__(self):
        super().__init__("baostock_basic")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch stock basic info from baostock."""
        import baostock as bs

        lg = bs.login()
        if lg.error_code != "0":
            bs.logout()
            raise RuntimeError(f"baostock login failed: {lg.error_msg}")

        try:
            rs = bs.query_stock_basic()
            if rs.error_code != "0":
                raise RuntimeError(f"query_stock_basic failed: {rs.error_msg}")

            rows: list[dict[str, Any]] = []
            while rs.next():
                row = rs.get_row_data()
                rows.append(row)

            # Convert to DataFrame for consistent column handling
            if not rows:
                return []
            df = pd.DataFrame(rows, columns=rs.fields)
            return df.to_dict(orient="records")
        finally:
            bs.logout()

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize baostock field names to model fields."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            validated.append({
                "code": str(row.get("code", "")),
                "code_name": str(row.get("code_name", "")) if row.get("code_name") else None,
                "ipo_date": str(row.get("ipoDate", "")) if row.get("ipoDate") else None,
                "out_date": str(row.get("outDate", "")) if row.get("outDate") else None,
                "type": str(row.get("type", "")) if row.get("type") else None,
                "status": str(row.get("status", "")) if row.get("status") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records, deduplicating by code."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefBaostockBasic).filter_by(
                    code=rec["code"]
                ).first()
                if existing:
                    continue
                session.add(RefBaostockBasic(**rec))
                written += 1
        return written
