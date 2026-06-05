"""融资融券标的 — MarginSecsCollector

Tushare margin_secs API — 融资融券标的列表（每日盘前更新）。

API limit: 6000 rows per call. Exchange-based iteration with checkpoint.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMarginSecs
from src.collectors.base import BaseTushareCollector

logger = logging.getLogger(__name__)


class MarginSecsCollector(BaseTushareCollector):
    """融资融券标的 collector — 按交易所+日期逐天回填."""

    EXCHANGES = ["SSE", "SZSE", "BSE"]

    def __init__(self, token: str):
        super().__init__("margin_secs", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("margin_secs", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        import math
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")) if row.get("name") is not None and not (isinstance(row.get("name"), float) and math.isnan(row.get("name"))) else "",
                "exchange": str(row.get("exchange", "")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawMarginSecs, records, ["trade_date", "ts_code"])

    # ── Date-loop Run ──────────────────────────────

    def run(self, **kwargs) -> dict:
        """Loop forward through trading days, fetch per exchange, validate, store."""
        d = datetime(2010, 1, 1)
        today = datetime.now()
        dp = []
        while d <= today:
            if d.weekday() < 5:
                dp.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)

        last_date = self.get_checkpoint_date()

        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0}
        t0 = time.time()
        total_days = len(dp)

        for i, d in enumerate(dp):
            if last_date and d <= last_date:
                continue

            for ex in self.EXCHANGES:
                time.sleep(0.20)
                try:
                    raw = self.fetch(trade_date=d, exchange=ex)
                except Exception:
                    stats["errors"] += 1
                    continue

                if not raw:
                    continue

                validated = self.validate(raw)
                written = self.store_raw(validated)
                stats["fetched"] += len(validated)
                stats["written"] += written

            stats["days"] += 1
            self._update_checkpoint(d, 0)  # track date, not per-day count

            if stats["days"] % 50 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("margin_secs DONE: %d days, %s rows, %.0fs",
                    stats["days"], f"{stats['written']:,}", elapsed)
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
