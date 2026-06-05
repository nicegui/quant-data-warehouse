"""同花顺行业资金流向 — MoneyflowIndThsCollector

Tushare moneyflow_ind_ths API — 行业级别逐日资金流向。
~90 个行业/天，含领涨股 + 行业指数。
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMoneyflowIndThs
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class MoneyflowIndThsCollector(BaseTushareCollector):
    """同花顺行业资金流向 collector — 按交易日逐天回填."""

    def __init__(self, token: str):
        super().__init__("moneyflow_ind_ths", token)

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
        return self.api_call("moneyflow_ind_ths", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            lead = row.get("lead_stock")
            if lead is None or (isinstance(lead, float) and math.isnan(lead)):
                lead = ""
            rec = {
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "industry": str(row.get("industry", "")) if row.get("industry") else "",
                "lead_stock": str(lead),
                "close": _f(row.get("close")),
                "pct_change": _f(row.get("pct_change")),
                "company_num": int(row["company_num"]) if row.get("company_num") is not None else None,
                "pct_change_stock": _f(row.get("pct_change_stock")),
                "close_price": _f(row.get("close_price")),
                "net_buy_amount": _f(row.get("net_buy_amount")),
                "net_sell_amount": _f(row.get("net_sell_amount")),
                "net_amount": _f(row.get("net_amount")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawMoneyflowIndThs, records, ["trade_date", "ts_code"])

    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query("SELECT DISTINCT trade_date FROM raw_moneyflow_ind_ths")
            return {row[0] for row in result["rows"]}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()

        d = datetime(2025, 12, 1)  # THS行业数据 ~2025-12 开始
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

            if stats["days"] % 50 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("moneyflow_ind_ths DONE: %d days, %s rows, %d skipped, %.0fs",
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
