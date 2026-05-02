"""大宗商品指数 — DcIndexCollector

Tushare dc_index API — 东方财富概念/行业板块指数行情.
"""
from __future__ import annotations

import json
import math
from typing import Any

from src.db.session import db_session
from src.models.dc_index import RawDcIndex
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class DcIndexCollector(BaseTushareCollector):
    """大宗商品指数 collector (日期循环)."""

    IDX_TYPES = ["概念板块", "行业板块", "地域板块"]

    def __init__(self, token: str):
        super().__init__("dc_index", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("dc_index", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "name": row.get("name", ""),
                "leading": row.get("leading", ""),
                "leading_code": row.get("leading_code", ""),
                "pct_change": _f(row.get("pct_change")),
                "leading_pct": _f(row.get("leading_pct")),
                "total_mv": _f(row.get("total_mv")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "up_num": None if row.get("up_num") is None or (isinstance(row.get("up_num"), float) and math.isnan(row.get("up_num"))) else int(row.get("up_num")),
                "down_num": None if row.get("down_num") is None or (isinstance(row.get("down_num"), float) and math.isnan(row.get("down_num"))) else int(row.get("down_num")),
                "idx_type": row.get("idx_type", ""),
                "level": row.get("level"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawDcIndex).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawDcIndex(**rec))
                written += 1
        return written

    def run(self, **kwargs) -> dict:
        import logging, time
        from datetime import datetime as dt, timedelta
        logger = logging.getLogger(__name__)

        last_date = self.get_checkpoint_date()
        d = dt(2018, 1, 1) if not last_date else dt.strptime(last_date, "%Y%m%d")
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

            for idx_type in self.IDX_TYPES:
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
                eta = 0
                remaining = sum(1 for _d in (dt(2018,1,1) + timedelta(days=x) for x in range((today - dt(2018,1,1)).days + 1)) if _d.weekday() < 5 and _d.strftime("%Y%m%d") > date_str)
                if rate > 0:
                    eta = remaining / rate
                logger.info("[%s] %d days, %s rows | %.1f d/s ETA %.0fs",
                            date_str, stats["days"], f"{stats['written']:,}", rate, eta)

        elapsed = time.time() - t0
        logger.info("dc_index DONE: %d days, %s rows, %d errors, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["errors"], elapsed)
        return {
            "status": "success" if stats["errors"] < stats["days"] * 0.1 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
