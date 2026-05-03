"""基金仓位 — FundPositionCollector

Uses curl + CSRF token to bypass legulegu.com SSL issues.
Covers three fund types: stock (股票型), linghuo (灵活混合型), pingheng (平衡混合型).
"""

from __future__ import annotations

import json
import re
import subprocess
from hashlib import md5
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from src.models.macro_fund import RawFundPosition
from src.collectors.base import BaseCollector


# Fund type config: (api_type, fund_type, display_name)
FUND_TYPES = [
    ("pos_stock", "stock", "股票型"),
    ("pos_linghuo", "linghuo", "灵活混合型"),
    ("pos_pingheng", "pingheng", "平衡混合型"),
]


class FundPositionCollector(BaseCollector):
    """Collect fund position estimates from legulegu.com via curl."""

    def __init__(self):
        super().__init__("fund_position")
        self._csrf: str | None = None
        self._cookie_file: str = "/tmp/lg_cookies.txt"

    # ── Shared helpers ──

    def _ensure_csrf(self) -> str:
        """Fetch CSRF token from legulegu page if not cached."""
        if self._csrf:
            return self._csrf

        result = subprocess.run(
            ["curl", "-sS", "--insecure", "-c", self._cookie_file, "--max-time", "20",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             "https://legulegu.com/stockdata/fund-position/pos-pingheng"],
            capture_output=True, text=True, timeout=25
        )
        match = re.search(r'<meta name="_csrf" content="([^"]+)"', result.stdout)
        if not match:
            raise RuntimeError(f"CSRF token not found in page (len={len(result.stdout)})")
        self._csrf = match.group(1)
        return self._csrf

    def _token(self) -> str:
        """Generate md5(date) token."""
        return md5(datetime.now().date().isoformat().encode("utf-8")).hexdigest()

    def _call_api(self, api_type: str) -> list[dict[str, Any]]:
        """Call legulegu API for one fund type."""
        csrf = self._ensure_csrf()
        params = urlencode({
            "token": self._token(),
            "type": api_type,
            "category": "总仓位",
            "marketId": "5",
        })
        url = f"https://legulegu.com/api/stockdata/fund-position?{params}"

        result = subprocess.run(
            ["curl", "-sS", "--insecure", "-b", self._cookie_file, "--max-time", "30",
             "-H", f"X-CSRF-Token: {csrf}",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=35
        )
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr[:200]}")
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"API returned non-JSON: {result.stdout[:300]}")
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"API error: {data}")
        return data

    # ── Collector interface ──

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch all fund types. Returns raw API records with _fund_type tag."""
        rows: list[dict[str, Any]] = []
        for api_type, fund_type, _display in FUND_TYPES:
            try:
                data = self._call_api(api_type)
                for r in data:
                    r["_fund_type"] = fund_type
                rows.extend(data)
            except Exception as e:
                print(f"[fund_position] {fund_type} fetch failed: {e}")
        return rows

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize and type-coerce."""
        validated: list[dict[str, Any]] = []
        for r in raw:
            rec = {
                "trade_date": str(r.get("date", "")),
                "fund_type": str(r.get("_fund_type", "")),
                "position": self._safe_float(r.get("position")),
                "close": self._safe_float(r.get("close")),
                "raw_json": json.dumps(r, ensure_ascii=False, default=str),
            }
            if rec["trade_date"] and rec["fund_type"]:
                validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store via _store_dedup upsert."""
        if not records:
            return 0
        return self._store_dedup(RawFundPosition, records, ["trade_date", "fund_type"])

    # ── Static helpers ──

    @staticmethod
    def _safe_float(val: Any) -> float | None:
        if val is None or val == ".00" or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
