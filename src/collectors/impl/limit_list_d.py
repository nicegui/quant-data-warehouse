"""涨跌停列表新版 — LimitListDCollector

Tushare limit_list_d API — 每日涨跌停/炸板数据。
数据从 2020 开始，每天循环 U/D/Z 三种 limit_type。
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawLimitListD
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)

LIMIT_TYPES = ["U", "D", "Z"]


class LimitListDCollector(BaseTushareCollector):
    """涨跌停列表新版 collector — 按交易日+limit_type 逐天回填."""

    def __init__(self, token: str):
        super().__init__("limit_list_d", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              limit_type: str = "U", **kwargs) -> list[dict]:
        params: dict[str, Any] = {"limit_type": limit_type}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("limit_list_d", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "industry": str(row.get("industry", "")) if row.get("industry") else "",
                "name": str(row.get("name", "")) if row.get("name") else "",
                "close": _f(row.get("close")),
                "pct_chg": _f(row.get("pct_chg")),
                "amount": _f(row.get("amount")),
                "limit_amount": _f(row.get("limit_amount")),
                "float_mv": _f(row.get("float_mv")),
                "total_mv": _f(row.get("total_mv")),
                "turnover_ratio": _f(row.get("turnover_ratio")),
                "fd_amount": _f(row.get("fd_amount")),
                "first_time": str(row.get("first_time", "")) if row.get("first_time") else None,
                "last_time": str(row.get("last_time", "")) if row.get("last_time") else None,
                "open_times": int(row["open_times"]) if row.get("open_times") is not None and not (isinstance(row.get("open_times"), float) and math.isnan(row["open_times"])) else None,
                "up_stat": str(row.get("up_stat", "")) if row.get("up_stat") else "",
                "limit_times": int(row["limit_times"]) if row.get("limit_times") is not None and not (isinstance(row.get("limit_times"), float) and math.isnan(row["limit_times"])) else None,
                "lim": str(row.get("limit", "")) if row.get("limit") else "",
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawLimitListD, records, ["trade_date", "ts_code", "lim"])

    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query("SELECT DISTINCT trade_date FROM raw_limit_list_d")
            return {row[0] for row in result["rows"]}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()

        d = datetime(2020, 1, 1)
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
            day_written = 0

            for lt in LIMIT_TYPES:
                try:
                    raw = self.fetch(trade_date=d, limit_type=lt)
                except Exception:
                    stats["errors"] += 1
                    continue

                if not raw:
                    continue

                validated = self.validate(raw)
                written = self.store_raw(validated)
                stats["fetched"] += len(validated)
                stats["written"] += written
                day_written += written

            if day_written:
                stats["days"] += 1
                self._update_checkpoint(d, day_written)

            if stats["days"] % 100 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("limit_list_d DONE: %d days, %s rows, %d skipped, %.0fs",
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
