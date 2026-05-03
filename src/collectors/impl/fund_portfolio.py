"""公募基金重仓持股 — FundPortfolioCollector

Batch-pulls fund_portfolio_hold_em() for stock-type and hybrid funds.
Uses checkpoint_key to resume across sessions.
"""

from __future__ import annotations

import json
import time
from typing import Any

from src.models.macro_fund import RawFundHolding
from src.collectors.base import BaseAKShareCollector


class FundPortfolioCollector(BaseAKShareCollector):
    """Collect fund heavy-holding stocks from Eastmoney."""

    checkpoint_key = "fund_portfolio"

    def __init__(self):
        super().__init__("fund_portfolio")

    def _get_stock_fund_codes(self) -> list[str]:
        """Get all stock-type fund codes from akshare."""
        df = self.ak.fund_open_fund_rank_em(symbol="股票型")
        codes = sorted(df["基金代码"].unique())
        print(f"[fund_portfolio] {len(codes)} stock-type funds found")
        return [str(c) for c in codes]

    def _get_hybrid_fund_codes(self) -> list[str]:
        """Get hybrid fund codes (biased toward stock-heavy)."""
        try:
            df = self.ak.fund_open_fund_rank_em(symbol="混合型")
            codes = sorted(df["基金代码"].unique())
            print(f"[fund_portfolio] {len(codes)} hybrid-type funds found (sampling...)")
            # Sample: take first 2000 to keep runtime reasonable
            return [str(c) for c in codes[:2000]]
        except Exception:
            return []

    # ── Collector interface ──

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Batch pull holdings for all stock-type funds across 2020-2025."""
        codes = self._get_stock_fund_codes()
        years = kwargs.get("years", ["2020", "2021", "2022", "2023", "2024", "2025"])

        all_rows: list[dict[str, Any]] = []
        total = len(codes) * len(years)
        done = 0
        errors = 0

        for code in codes:
            for year in years:
                try:
                    df = self.ak.fund_portfolio_hold_em(symbol=code, date=year)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            all_rows.append({
                                "_fund_code": code,
                                "_year": year,
                                **row.to_dict(),
                            })
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"[fund_portfolio] error {code}/{year}: {e}")
                done += 1
                time.sleep(0.15)  # rate limit

            if done % 200 == 0:
                print(f"[fund_portfolio] progress: {done}/{total}, "
                      f"rows={len(all_rows)}, errors={errors}")

        print(f"[fund_portfolio] Done: {done}/{total}, {len(all_rows)} rows, {errors} errors")
        return all_rows

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize field names from Chinese to English model columns."""
        validated: list[dict[str, Any]] = []
        for r in raw:
            rec = {
                "fund_code": str(r.get("_fund_code", "")),
                "stock_code": str(r.get("股票代码", "")),
                "stock_name": str(r.get("股票名称", "")) if r.get("股票名称") else None,
                "weight": self._safe_float(r.get("占净值比例")),
                "shares": self._safe_float(r.get("持股数")),
                "market_value": self._safe_float(r.get("持仓市值")),
                "quarter": str(r.get("季度", "")),
            }
            if rec["fund_code"] and rec["stock_code"]:
                validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        return self._store_dedup(RawFundHolding, records, ["fund_code", "stock_code", "quarter"])
