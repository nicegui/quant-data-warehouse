"""龙虎榜明细 — TopListCollector

Tushare top_list API — 龙虎榜每日交易明细。
2005年至今，按交易日逐天回填。
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawTopList
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class TopListCollector(BaseTushareCollector):
    """龙虎榜明细 collector — 按交易日逐天回填."""

    def __init__(self, token: str):
        super().__init__("top_list", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("top_list", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")) if row.get("name") else "",
                "reason": str(row.get("reason", "")) if row.get("reason") else "",
                "close": _f(row.get("close")),
                "pct_change": _f(row.get("pct_change")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "amount": _f(row.get("amount")),
                "l_sell": _f(row.get("l_sell")),
                "l_buy": _f(row.get("l_buy")),
                "l_amount": _f(row.get("l_amount")),
                "net_amount": _f(row.get("net_amount")),
                "net_rate": _f(row.get("net_rate")),
                "amount_rate": _f(row.get("amount_rate")),
                "float_values": _f(row.get("float_values")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawTopList, records, ["ts_code", "trade_date"])


    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT DISTINCT trade_date FROM raw_top_list")
            ).fetchall()
            session.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()

        d = datetime(2005, 1, 1)
        today = datetime.now()
        dp = []
        while d <= today:
            if d.weekday() < 5:
                dp.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)

        last_date = self.get_checkpoint_date()

        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0, "skipped": 0}
        t0 = time.time()
        total_days = len(dp)

        for i, d in enumerate(dp):
            if last_date and d <= last_date:
                stats["skipped"] += 1
                continue
            if d in existing:
                continue

            time.sleep(0.20)
            try:
                raw = self.fetch(trade_date=d)
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
            self._update_checkpoint(d, written)

            if stats["days"] % 100 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("top_list DONE: %d days, %s rows, %d skipped, %.0fs",
                    stats["days"], f"{stats['written']:,}",
                    stats["skipped"], elapsed)
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "skipped": stats["skipped"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
