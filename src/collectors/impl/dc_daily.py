"""东方财富板块日线 — DcDailyCollector

Tushare dc_daily API — 日期驱动 × 3种板块类型。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime as dt, timedelta
from typing import Any

from src.db.session import db_session
from src.models.dc_daily import RawDcDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)

IDX_TYPES = ["概念板块", "行业板块", "地域板块"]


class DcDailyCollector(BaseTushareCollector):
    """东方财富板块日线 collector (日期驱动)."""

    def __init__(self, token: str):
        super().__init__("dc_daily", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("dc_daily", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": str(row.get("ts_code", "")),
                "trade_date": str(row.get("trade_date", "")),
                "close": _f(row.get("close")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "change": _f(row.get("change")),
                "pct_change": _f(row.get("pct_change")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "swing": _f(row.get("swing")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "category": str(row.get("category", "")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawDcDaily, records, ["ts_code", "trade_date"])

    def run(self, **kwargs) -> dict:
        last_date = self.get_checkpoint_date()
        d = dt(2020, 1, 1) if not last_date else dt.strptime(last_date, "%Y%m%d")
        today = dt.now()
        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0}
        t0 = time.time()

        while d <= today:
            if d.weekday() >= 5:
                d += timedelta(days=1)
                continue

            date_str = d.strftime("%Y%m%d")
            d += timedelta(days=1)

            if last_date and date_str <= last_date:
                continue

            time.sleep(0.20)
            day_fetched = 0

            for idx_type in IDX_TYPES:
                try:
                    raw = self.fetch(trade_date=date_str, idx_type=idx_type)
                except Exception:
                    stats["errors"] += 1
                    continue

                if not raw:
                    continue

                validated = self.validate(raw)
                written = self.store_raw(validated)
                stats["fetched"] += len(validated)
                stats["written"] += written
                day_fetched += len(validated)

            stats["days"] += 1
            self._update_checkpoint(date_str, day_fetched)

            if stats["days"] % 100 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                logger.info("[%s] %d days, %s rows | %.1f d/s ETA ~",
                            date_str, stats["days"], f"{stats['written']:,}", rate)

        elapsed = time.time() - t0
        logger.info("dc_daily DONE: %d days, %s rows, %d errors, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["errors"], elapsed)
        return {
            "status": "success" if stats["errors"] < max(stats["days"], 1) * 0.1 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
