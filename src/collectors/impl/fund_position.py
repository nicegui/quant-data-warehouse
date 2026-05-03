"""基金仓位 + 公募持仓 collector."""
from __future__ import annotations
import json
import time
from typing import Any
from src.collectors.base import BaseAKShareCollector
from src.models.macro_fund import RawFundPosition, RawFundHolding


class FundPositionCollector(BaseAKShareCollector):
    """基金仓位估算 (乐股)."""

    def __init__(self):
        super().__init__("fund_position")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self._ak_fetch(self.ak.fund_balance_position_lg)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not raw:
            return []
        validated = []
        for row in raw:
            rec = {
                "trade_date": self._safe_str(row.get("日期") or row.get("date")),
                "stock_fund_pct": self._safe_float(row.get("股票型")),
                "hybrid_fund_pct": self._safe_float(row.get("混合型")),
                "total_pct": self._safe_float(row.get("总仓位")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawFundPosition, records, ["trade_date"])


class FundHoldingCollector(BaseAKShareCollector):
    """公募基金持仓明细.

    Fetches holdings for all active funds from Tushare's fund_basic list.
    """

    def __init__(self):
        super().__init__("fund_holding")

    def fetch(self, fund_code: str = "000001", date: str = "2025", **kwargs) -> list[dict[str, Any]]:
        return self._ak_fetch(self.ak.fund_portfolio_hold_em, symbol=fund_code, date=date)

    def validate(self, raw: list[dict[str, Any]], fund_code: str = "") -> list[dict[str, Any]]:
        if not raw:
            return []
        validated = []
        for row in raw:
            rec = {
                "fund_code": fund_code,
                "stock_code": self._safe_str(row.get("股票代码")),
                "stock_name": self._safe_str(row.get("股票名称")),
                "report_date": self._safe_str(row.get("报告期")),
                "hold_value": self._safe_float(row.get("持股市值")),
                "hold_pct": self._safe_float(row.get("占净值比例") or row.get("占净值比")),
                "shares": self._safe_float(row.get("持股数")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawFundHolding, records, ["fund_code", "stock_code", "report_date"])

    def run_batch(self, date: str = "2025", limit: int = 100) -> int:
        """Batch fetch holdings for top funds."""
        from src.db.session import db_session
        from sqlalchemy import text

        with db_session() as s:
            r = s.execute(
                text(
                    "SELECT DISTINCT ts_code FROM fund_basic "
                    "WHERE market IN ('E','O') AND status='L' LIMIT :n"
                ),
                {"n": limit},
            )
            fund_codes = [row[0] for row in r]

        if not fund_codes:
            print("[fund_holding] No funds found in fund_basic")
            return 0

        all_written = 0
        for i, fc in enumerate(fund_codes):
            raw = self.fetch(fund_code=fc, date=date)
            if not raw:
                continue
            valid = self.validate(raw, fund_code=fc)
            written = self.store_raw(valid)
            all_written += written
            if (i + 1) % 20 == 0:
                print(f"[fund_holding] {i+1}/{len(fund_codes)} funds, {all_written} holdings")
            time.sleep(0.3)

        print(f"[fund_holding] Done: {len(fund_codes)} funds, {all_written} holdings total")
        return all_written
