"""同花顺涨跌停榜单 — LimitListThsCollector

Tushare limit_list_ths API — 同花顺每日涨跌停榜单。
数据从 2023-11-01 开始，每天循环 5 种 limit_type。
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawLimitListThs
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)

LIMIT_TYPES = ["涨停池", "连扳池", "冲刺涨停", "炸板池", "跌停池"]


class LimitListThsCollector(BaseTushareCollector):
    """同花顺涨跌停榜单 collector — 按交易日+limit_type 逐天回填."""

    def __init__(self, token: str):
        super().__init__("limit_list_ths", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              limit_type: str = "涨停池", **kwargs) -> list[dict]:
        params: dict[str, Any] = {"limit_type": limit_type}
        if trade_date:
            params["trade_date"] = trade_date
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("limit_list_ths", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")) if row.get("name") else "",
                "price": _f(row.get("price")),
                "pct_chg": _f(row.get("pct_chg")),
                "open_num": int(row["open_num"]) if row.get("open_num") is not None and not (isinstance(row.get("open_num"), float) and math.isnan(row["open_num"])) else None,
                "lu_desc": str(row.get("lu_desc", "")) if row.get("lu_desc") else "",
                "limit_type": str(row.get("limit_type", "")),
                "tag": str(row.get("tag", "")) if row.get("tag") else "",
                "status": str(row.get("status", "")) if row.get("status") else "",
                "first_lu_time": str(row.get("first_lu_time", "")) if row.get("first_lu_time") else None,
                "last_lu_time": str(row.get("last_lu_time", "")) if row.get("last_lu_time") else None,
                "first_ld_time": str(row.get("first_ld_time", "")) if row.get("first_ld_time") else None,
                "last_ld_time": str(row.get("last_ld_time", "")) if row.get("last_ld_time") else None,
                "limit_order": _f(row.get("limit_order")),
                "limit_amount": _f(row.get("limit_amount")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "free_float": _f(row.get("free_float")),
                "lu_limit_order": _f(row.get("lu_limit_order")),
                "limit_up_suc_rate": _f(row.get("limit_up_suc_rate")),
                "turnover": _f(row.get("turnover")),
                "rise_rate": _f(row.get("rise_rate")),
                "sum_float": _f(row.get("sum_float")),
                "market_type": str(row.get("market_type", "")) if row.get("market_type") else "",
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawLimitListThs).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                    limit_type=rec["limit_type"],
                ).first()
                if existing:
                    continue
                session.add(RawLimitListThs(**rec))
                written += 1
        return written

    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT DISTINCT trade_date FROM raw_limit_list_ths")
            ).fetchall()
            session.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()

        d = datetime(2023, 11, 1)  # Data starts 2023-11-01
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

            if stats["days"] % 50 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("limit_list_ths DONE: %d days, %s rows, %d skipped, %.0fs",
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
