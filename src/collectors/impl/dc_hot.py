"""东方财富热榜 — DcHotCollector

Tushare dc_hot API — 东方财富App人气榜/飙升榜，日期驱动 × 市场 × 热点类型。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime as dt, timedelta
from typing import Any

from src.db.session import db_session
from src.models.dc_hot import RawDcHot
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)

MARKETS = ["A股市场", "ETF基金", "港股市场", "美股市场"]
HOT_TYPES = ["人气榜", "飙升榜"]


class DcHotCollector(BaseTushareCollector):
    """东方财富热榜 collector (日期驱动 × 市场 × 热点类型)."""

    def __init__(self, token: str):
        super().__init__("dc_hot", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("dc_hot", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "data_type": str(row.get("data_type", "")),
                "ts_code": str(row.get("ts_code", "")),
                "ts_name": str(row.get("ts_name", "")),
                "rank": row.get("rank"),
                "pct_change": _f(row.get("pct_change")),
                "current_price": _f(row.get("current_price")),
                "rank_time": str(row.get("rank_time", "")),
                "market": str(row.get("market", "")),
                "hot_type": str(row.get("hot_type", "")),
                "hot": _f(row.get("hot")),
                "concept": str(row.get("concept", "")) if row.get("concept") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        if not records:
            return 0
        written = 0
        with db_session() as session:
            keys = {(r["trade_date"], r["ts_code"], r["market"], r["hot_type"], r["rank_time"]) for r in records}
            existing_rows = session.query(
                RawDcHot.trade_date, RawDcHot.ts_code, RawDcHot.market,
                RawDcHot.hot_type, RawDcHot.rank_time,
            ).filter(
                RawDcHot.trade_date.in_([k[0] for k in keys])
            ).all()
            existing_set = {(r.trade_date, r.ts_code, r.market, r.hot_type, r.rank_time) for r in existing_rows}
            for rec in records:
                key = (rec["trade_date"], rec["ts_code"], rec["market"], rec["hot_type"], rec["rank_time"])
                if key in existing_set:
                    continue
                session.add(RawDcHot(**rec))
                written += 1
        return written

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

            for market in MARKETS:
                for hot_type in HOT_TYPES:
                    try:
                        raw = self.fetch(trade_date=date_str, market=market,
                                         hot_type=hot_type, is_new="Y")
                    except Exception:
                        stats["errors"] += 1
                        continue

                    if not raw:
                        continue

                    # Inject market/hot_type into each record
                    for row in raw:
                        row["market"] = market
                        row["hot_type"] = hot_type

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
                logger.info("[%s] %d days, %s rows | %.1f d/s",
                            date_str, stats["days"], f"{stats['written']:,}", rate)

        elapsed = time.time() - t0
        logger.info("dc_hot DONE: %d days, %s rows, %d errors, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["errors"], elapsed)
        return {
            "status": "success" if stats["errors"] < max(stats["days"], 1) * 0.1 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
