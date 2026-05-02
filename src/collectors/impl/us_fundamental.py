"""美股基本面 — UsFundamentalCollector

Non-Tushare collector using yfinance for US stock fundamentals.
Supports: dividends, splits, recommendations, institutional_holders, info.
Each sub_api has its own fetch/validate/store pathway.
"""
from __future__ import annotations

import json
import sys
from typing import Any

import pandas as pd

from src.models.us_fundamental import (
    RawUsDividend,
    RawUsSplit,
    RawUsRecommendation,
    RawUsInstitutional,
    RawUsInfo,
)
from src.collectors.base import BaseYFinanceCollector


class UsFundamentalCollector(BaseYFinanceCollector):
    """美股基本面 collector via yfinance (non-Tushare)."""

    def __init__(self):
        super().__init__("us_fundamental")

    def fetch(self, symbol: str = "AAPL", sub_api: str = "info", **kwargs) -> list[dict[str, Any]]:
        """Fetch US fundamental data from yfinance.

        Args:
            symbol: ticker symbol (e.g. "AAPL", "MSFT")
            sub_api: one of "dividends", "splits", "recommendations",
                     "institutional_holders", "info"
        """
        try:
            ticker = self._get_ticker(symbol)

            if sub_api == "dividends":
                return self._fetch_series(ticker.dividends, symbol, "dividend")
            elif sub_api == "splits":
                return self._fetch_series(ticker.splits, symbol, "split_ratio")
            elif sub_api == "recommendations":
                return self._fetch_df(ticker.recommendations, symbol)
            elif sub_api == "institutional_holders":
                return self._fetch_df(ticker.institutional_holders, symbol)
            elif sub_api == "info":
                info = ticker.info
                if info is None or not isinstance(info, dict):
                    return []
                info["_symbol"] = symbol
                return [info]
            else:
                raise ValueError(f"Unknown sub_api: {sub_api}")
        except Exception as e:
            msg = str(e).lower()
            if any(kw in msg for kw in ("rate limit", "too many", "429", "jsondecodeerror", "forbidden")):
                print(f"[WARNING] yfinance error for {symbol}/{sub_api}: {e}", file=sys.stderr)
                return []
            raise

    @staticmethod
    def _fetch_series(series, symbol: str, value_name: str) -> list[dict[str, Any]]:
        """Convert a pandas Series (dividends/splits) to list[dict]."""
        if series is None or (hasattr(series, "empty") and series.empty):
            return []
        rows: list[dict[str, Any]] = []
        for dt, val in series.items():
            date_str = str(dt).split(" ")[0] if hasattr(dt, "strftime") else str(dt)[:10]
            rows.append({
                "_symbol": symbol,
                "date": date_str,
                value_name: float(val),
            })
        return rows

    @staticmethod
    def _fetch_df(df, symbol: str) -> list[dict[str, Any]]:
        """Convert a pandas DataFrame to list[dict], normalizing timestamps."""
        if df is None or (hasattr(df, "empty") and df.empty):
            return []
        df = df.reset_index()
        records: list[dict[str, Any]] = df.to_dict(orient="records")
        for rec in records:
            rec["_symbol"] = symbol
            # Normalize Timestamp/date columns to string
            for key, val in list(rec.items()):
                if isinstance(val, pd.Timestamp):
                    rec[key] = val.strftime("%Y-%m-%d")
        return records

    # ── Validate: normalize yfinance field names to model fields ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize field names and coerce types. Delegates per shape."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = self._normalize(row)
            if rec:
                validated.append(rec)
        return validated

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any] | None:
        """Detect shape and normalize to model-compatible dict."""
        symbol = str(row.get("_symbol", ""))

        # dividends shape: has "dividend" + "date" keys
        if "dividend" in row:
            return {
                "symbol": symbol,
                "date": self._safe_str(row.get("date")),
                "dividend": self._safe_float(row.get("dividend")) or 0.0,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }

        # splits shape: has "split_ratio" + "date" keys
        if "split_ratio" in row:
            return {
                "symbol": symbol,
                "date": self._safe_str(row.get("date")),
                "split_ratio": self._safe_float(row.get("split_ratio")) or 0.0,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }

        # recommendations shape: has "Firm" / "firm" / "To Grade" / "toGrade"
        if any(k in row for k in ("Firm", "firm", "To Grade", "toGrade")):
            date_val = row.get("Date") or row.get("date") or ""
            if isinstance(date_val, pd.Timestamp):
                date_val = date_val.strftime("%Y-%m-%d")
            return {
                "symbol": symbol,
                "date": self._safe_str(date_val),
                "firm": self._safe_str(row.get("Firm") or row.get("firm")),
                "to_grade": self._safe_str(row.get("To Grade") or row.get("toGrade")),
                "from_grade": self._safe_str(row.get("From Grade") or row.get("fromGrade")),
                "action": self._safe_str(row.get("Action") or row.get("action")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }

        # institutional_holders shape: has "Holder" / "holder" / "pctHeld"
        if any(k in row for k in ("Holder", "holder", "pctHeld")):
            date_val = row.get("Date Reported") or row.get("dateReported") or ""
            if isinstance(date_val, pd.Timestamp):
                date_val = date_val.strftime("%Y-%m-%d")
            return {
                "symbol": symbol,
                "date_reported": self._safe_str(date_val),
                "holder": self._safe_str(row.get("Holder") or row.get("holder")),
                "pct_held": self._safe_float(row.get("pctHeld") or row.get("pctHeld")),
                "shares": self._safe_float(row.get("Shares") or row.get("shares")),
                "value": self._safe_float(row.get("Value") or row.get("value")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }

        # info shape: dict from ticker.info — has "sector"/"industry"/"marketCap" etc.
        if isinstance(row, dict) and any(
            k in row for k in ("sector", "industry", "marketCap", "longBusinessSummary")
        ):
            return {
                "symbol": symbol,
                "sector": self._safe_str(row.get("sector")),
                "industry": self._safe_str(row.get("industry")),
                "market_cap": self._safe_float(row.get("marketCap")),
                "employees": int(row["fullTimeEmployees"]) if row.get("fullTimeEmployees") is not None else None,
                "country": self._safe_str(row.get("country")),
                "website": self._safe_str(row.get("website")),
                "long_business_summary": self._safe_str(row.get("longBusinessSummary")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }

        return None

    # ── Store: route to correct table ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records into the correct raw table."""
        if not records:
            return 0

        first = records[0]
        if "dividend" in first:
            return self._store_dedup(RawUsDividend, records, ["symbol", "date"])
        if "split_ratio" in first:
            return self._store_dedup(RawUsSplit, records, ["symbol", "date"])
        if "firm" in first:
            return self._store_dedup(RawUsRecommendation, records, ["symbol", "date", "firm"])
        if "holder" in first:
            return self._store_dedup(RawUsInstitutional, records, ["symbol", "date_reported", "holder"])
        if "market_cap" in first:
            return self._store_dedup(RawUsInfo, records, ["symbol"])
        return 0
