"""北向资金 — MoneyflowHsgtCollector

Tushare moneyflow_hsgt API — 沪深港通资金流向 (北向/南向资金).
单日单行数据，checkpoint 断点续传。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMoneyflowHsgt
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class MoneyflowHsgtCollector(BaseTushareCollector):
    """北向资金 collector — 按交易日逐天回填."""

    def __init__(self, token: str):
        super().__init__("moneyflow_hsgt", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", start_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if not params and trade_date:
            params["trade_date"] = trade_date
        return self.api_call("moneyflow_hsgt", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ggt_ss": _f(row.get("ggt_ss")),
                "ggt_sz": _f(row.get("ggt_sz")),
                "hgt": _f(row.get("hgt")),
                "sgt": _f(row.get("sgt")),
                "north_money": _f(row.get("north_money")),
                "south_money": _f(row.get("south_money")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawMoneyflowHsgt, records, ["trade_date"])


    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT DISTINCT trade_date FROM raw_moneyflow_hsgt")
            ).fetchall()
            session.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()

        d = datetime(2017, 1, 1)
        today = datetime.now()
        dp = []
        while d <= today:
            if d.weekday() < 5:
                dp.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)

        last_date = self.get_checkpoint_date()

        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0, "skipped": 0}
        t0 = time.time()

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

        elapsed = time.time() - t0
        logger.info("moneyflow_hsgt DONE: %d days, %s rows, %d skipped, %.0fs",
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
