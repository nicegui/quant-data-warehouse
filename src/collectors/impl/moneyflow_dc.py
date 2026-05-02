"""东方财富个股资金流向 — MoneyflowDcCollector

Tushare moneyflow_dc API — 东方财富版逐日全市场资金流向。
数据从 2023-09-11 开始，每天 ~5400 条，含超大单分类。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMoneyflowDc
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class MoneyflowDcCollector(BaseTushareCollector):
    """东方财富个股资金流向 collector — 按交易日逐天回填."""

    def __init__(self, token: str):
        super().__init__("moneyflow_dc", token)

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
        return self.api_call("moneyflow_dc", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")) if row.get("name") else "",
                "pct_change": _f(row.get("pct_change")),
                "close": _f(row.get("close")),
                "net_amount": _f(row.get("net_amount")),
                "net_amount_rate": _f(row.get("net_amount_rate")),
                "buy_elg_amount": _f(row.get("buy_elg_amount")),
                "buy_elg_amount_rate": _f(row.get("buy_elg_amount_rate")),
                "buy_lg_amount": _f(row.get("buy_lg_amount")),
                "buy_lg_amount_rate": _f(row.get("buy_lg_amount_rate")),
                "buy_md_amount": _f(row.get("buy_md_amount")),
                "buy_md_amount_rate": _f(row.get("buy_md_amount_rate")),
                "buy_sm_amount": _f(row.get("buy_sm_amount")),
                "buy_sm_amount_rate": _f(row.get("buy_sm_amount_rate")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMoneyflowDc).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawMoneyflowDc(**rec))
                written += 1
        return written

    # ── Date-loop Run ──────────────────────────────

    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT DISTINCT trade_date FROM raw_moneyflow_dc")
            ).fetchall()
            session.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()

        # Data starts 2023-09-11
        d = datetime(2023, 9, 11)
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

            if stats["days"] % 20 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                eta = (total_days - i - 1) / rate if rate > 0 else 0
                logger.info("[day %s] %s/%s rows, %d days | %.1f d/s ETA %.0fs",
                            d, f"{stats['written']:,}", f"{stats['fetched']:,}",
                            stats["days"], rate, eta)

        elapsed = time.time() - t0
        logger.info("moneyflow_dc DONE: %d days, %s rows, %d skipped, %.0fs",
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
