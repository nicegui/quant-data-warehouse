"""东方财富板块成分 — DcMemberCollector

Tushare dc_member API — 东方财富概念/行业板块成分股。
日期驱动：逐日拉取当日全量成分，dedup 写入。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime as dt, timedelta
from typing import Any

from src.db.session import db_session
from src.models.dc_member import RawDcMember
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class DcMemberCollector(BaseTushareCollector):
    """东方财富板块成分 collector (日期驱动)."""

    def __init__(self, token: str):
        super().__init__("dc_member", token)

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
        return self.api_call("dc_member", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "con_code": str(row.get("con_code", "")),
                "name": str(row.get("name", "")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawDcMember, records, ["trade_date", "ts_code", "con_code"])

    def run(self, **kwargs) -> dict:
        last_date = self.get_checkpoint_date()
        d = dt(2015, 1, 1) if not last_date else dt.strptime(last_date, "%Y%m%d")
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
            try:
                raw = self.fetch(trade_date=date_str)
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
            self._update_checkpoint(date_str, written)

            if stats["days"] % 100 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                remaining = sum(1 for _d in (dt(2015,1,1) + timedelta(days=x)
                    for x in range((today - dt(2015,1,1)).days + 1))
                    if _d.weekday() < 5 and _d.strftime("%Y%m%d") > date_str)
                eta = remaining / rate if rate > 0 else 0
                logger.info("[%s] %d days, %s rows | %.1f d/s ETA %.0fs",
                            date_str, stats["days"], f"{stats['written']:,}", rate, eta)

        elapsed = time.time() - t0
        logger.info("dc_member DONE: %d days, %s rows, %d errors, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["errors"], elapsed)
        return {
            "status": "success" if stats["errors"] < max(stats["days"], 1) * 0.1 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
