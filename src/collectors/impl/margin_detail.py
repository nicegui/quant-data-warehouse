"""融资融券明细 — MarginDetailCollector

Tushare margin_detail API — 个股两融交易日明细。

API limit: 6000 rows per call. Date-based iteration with checkpoint.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMarginDetail
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class MarginDetailCollector(BaseTushareCollector):
    """融资融券明细 collector — 按交易日逐天回填."""

    def __init__(self, token: str):
        super().__init__("margin_detail", token)

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
        return self.api_call("margin_detail", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        import math
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")) if row.get("name") is not None and not (isinstance(row.get("name"), float) and math.isnan(row.get("name"))) else "",
                "rzye": _f(row.get("rzye")),
                "rqye": _f(row.get("rqye")),
                "rzmre": _f(row.get("rzmre")),
                "rqyl": _f(row.get("rqyl")),
                "rzche": _f(row.get("rzche")),
                "rqchl": _f(row.get("rqchl")),
                "rqmcl": _f(row.get("rqmcl")),
                "rzrqye": _f(row.get("rzrqye")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawMarginDetail, records, ["trade_date", "ts_code"])


    def run(self, **kwargs) -> dict:
        """Loop forward through trading days (oldest→newest), fetch, validate, store."""
        # Generate dates oldest→newest
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
                continue  # already processed

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

            # Progress every 50 days
            if stats["days"] % 50 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("margin_detail DONE: %d days, %s rows, %.0fs",
                    stats["days"], f"{stats['written']:,}", elapsed)
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }

    def _get_trade_cal(self) -> list[str] | None:
        """Get trading day list from trade_cal table or Tushare API."""
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT cal_date FROM raw_trade_cal WHERE is_open=1 AND exchange='SSE' ORDER BY cal_date")
            ).fetchall()
            session.close()
            return [r[0] for r in rows]
        except Exception:
            pass

        try:
            df = self.pro.trade_cal(exchange="SSE", is_open="1",
                                     start_date="20100101", end_date="20261231")
            return sorted(df["cal_date"].tolist())
        except Exception:
            return None

    @staticmethod
    def _fallback_dates() -> list[str]:
        """Generate all dates from 2010 to now (skip weekends)."""
        dates = []
        d = datetime.now()
        end = datetime(2010, 1, 1)
        while d >= end:
            if d.weekday() < 5:  # Mon-Fri
                dates.append(d.strftime("%Y%m%d"))
            d -= timedelta(days=1)
        return dates
