"""分析师一致预期 — AnalystForecastCollector

AKShare-backed snapshot collector for Eastmoney profit forecast consensus.
Fetches the full analyst consensus table (RPT_WEB_RESPREDICT) via direct API.
Each run overwrites the snapshot for the current date.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any

import requests

from src.collectors.base import BaseCollector
from src.models.analyst_forecast import RawAnalystForecast


class AnalystForecastCollector(BaseCollector):
    """分析师一致预期快照 collector.

    Uses direct Eastmoney HTTP API (not akshare wrapper) for efficiency.
    Snapshot key: (stock_code, snapshot_date).
    """

    API_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    # Page size — API allows up to 500
    PAGE_SIZE = 500

    def __init__(self):
        super().__init__("analyst_forecast")

    # ── Fetch ──

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch all analyst forecast records (paginated)."""
        all_rows: list[dict[str, Any]] = []
        page = 1

        while True:
            params = {
                "reportName": "RPT_WEB_RESPREDICT",
                "columns": "ALL",
                "pageNumber": str(page),
                "pageSize": str(self.PAGE_SIZE),
                "sortTypes": "-1",
                "sortColumns": "RATING_ORG_NUM",
            }
            try:
                r = requests.get(self.API_URL, params=params, timeout=30)
                data = r.json()
            except Exception:
                print(f"[analyst_forecast] Page {page}: request failed, stopping")
                break

            if not data.get("success"):
                print(f"[analyst_forecast] Page {page}: API returned success=false")
                break

            result = data.get("result")
            if not result:
                break

            page_data = result.get("data") or []
            all_rows.extend(page_data)

            total_pages = result.get("pages", 1)
            if page >= total_pages:
                break
            page += 1

        print(f"[analyst_forecast] Fetched {len(all_rows)} records across {page} pages")
        return all_rows

    # ── Validate ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Eastmoney fields to RawAnalystForecast fields."""
        if not raw:
            return []

        today = date.today().isoformat()
        validated: list[dict[str, Any]] = []

        for row in raw:
            rec = {
                "stock_code": (row.get("SECUCODE") or "").strip(),
                "stock_name": (row.get("SECURITY_NAME_ABBR") or "").strip(),
                "snapshot_date": today,
                # Ratings
                "rating_org_num": self._safe_int(row.get("RATING_ORG_NUM")),
                "rating_buy_num": self._safe_int(row.get("RATING_BUY_NUM")),
                "rating_add_num": self._safe_int(row.get("RATING_ADD_NUM")),
                "rating_neutral_num": self._safe_int(row.get("RATING_NEUTRAL_NUM")),
                "rating_reduce_num": self._safe_int(row.get("RATING_REDUCE_NUM")),
                "rating_sale_num": self._safe_int(row.get("RATING_SALE_NUM")),
                # EPS
                "year1": self._safe_int(row.get("YEAR1")),
                "eps1": self._safe_float(row.get("EPS1")),
                "year2": self._safe_int(row.get("YEAR2")),
                "eps2": self._safe_float(row.get("EPS2")),
                "year3": self._safe_int(row.get("YEAR3")),
                "eps3": self._safe_float(row.get("EPS3")),
                # Target
                "aim_price_max": self._safe_float(row.get("DEC_AIMPRICEMAX")),
                "aim_price_min": self._safe_float(row.get("DEC_AIMPRICEMIN")),
                # Industry
                "industry": (row.get("INDUSTRY_BOARD") or "").strip(),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)

        return validated

    # ── Store ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Dedup by (stock_code, snapshot_date)."""
        if not records:
            return 0
        return self._store_dedup(RawAnalystForecast, records, ["stock_code", "snapshot_date"])

    # ── Helpers ──

    @staticmethod
    def _safe_int(val: Any) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
