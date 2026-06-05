"""个股资金流向 — MoneyflowCollector

Tushare moneyflow API — 沪深A股逐日全市场资金流向。
数据开始于2010年，按交易日拉取，checkpoint 断点续传。
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMoneyflow
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class MoneyflowCollector(BaseTushareCollector):
    """个股资金流向 collector — 按交易日逐天回填."""

    def __init__(self, token: str):
        super().__init__("moneyflow", token)

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
        return self.api_call("moneyflow", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "buy_sm_vol": _f(row.get("buy_sm_vol")),
                "buy_sm_amount": _f(row.get("buy_sm_amount")),
                "sell_sm_vol": _f(row.get("sell_sm_vol")),
                "sell_sm_amount": _f(row.get("sell_sm_amount")),
                "buy_md_vol": _f(row.get("buy_md_vol")),
                "buy_md_amount": _f(row.get("buy_md_amount")),
                "sell_md_vol": _f(row.get("sell_md_vol")),
                "sell_md_amount": _f(row.get("sell_md_amount")),
                "buy_lg_vol": _f(row.get("buy_lg_vol")),
                "buy_lg_amount": _f(row.get("buy_lg_amount")),
                "sell_lg_vol": _f(row.get("sell_lg_vol")),
                "sell_lg_amount": _f(row.get("sell_lg_amount")),
                "buy_elg_vol": _f(row.get("buy_elg_vol")),
                "buy_elg_amount": _f(row.get("buy_elg_amount")),
                "sell_elg_vol": _f(row.get("sell_elg_vol")),
                "sell_elg_amount": _f(row.get("sell_elg_amount")),
                "net_mf_vol": _f(row.get("net_mf_vol")),
                "net_mf_amount": _f(row.get("net_mf_amount")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawMoneyflow, records, ["trade_date", "ts_code"])


    def _get_existing_dates(self) -> set[str]:
        """Return set of trade_dates that already have rows in DB."""
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT DISTINCT trade_date FROM raw_moneyflow")
            ).fetchall()
            session.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        """Loop forward through trading days (oldest→newest), fetch, validate, store.

        Skips days that already have data in DB, plus checkpoint for efficiency.
        """
        # Load existing dates from DB (fast skip)
        existing = self._get_existing_dates()

        # Generate dates oldest→newest
        d = datetime(2010, 1, 1)
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
            # Two-layer skip: checkpoint + DB check
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

            # Progress every 100 days
            if stats["days"] % 100 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("moneyflow DONE: %d days, %s rows, %d skipped, %.0fs",
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
