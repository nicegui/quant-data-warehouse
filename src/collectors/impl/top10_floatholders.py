"""十大流通股东 — Top10FloatHoldersCollector

Tushare top10_floatholders API — 前十大流通股东明细。
Per-stock API，本 collector 自动遍历全市场股票，支持 checkpoint 断点续传。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawStkHolderFloatTop
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class Top10FloatHoldersCollector(BaseTushareCollector):
    """十大流通股东 collector — 全市场遍历 + checkpoint 断点续传。"""

    def __init__(self, token: str):
        super().__init__("top10_floatholders", token)

    @property
    def checkpoint_key(self) -> str:
        return "ts_code"

    # ── Fetch ───────────────────────────────────────────

    def fetch(self, ts_code: str = "", ann_date: str = "",
              end_date: str = "", start_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        if end_date:
            params["end_date"] = end_date
        if start_date:
            params["start_date"] = start_date
        return self.api_call("top10_floatholders", **params)

    # ── Validate ────────────────────────────────────────

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "holder_name": row.get("holder_name", ""),
                "hold_amount": _f(row.get("hold_amount")),
                "hold_ratio": _f(row.get("hold_ratio")),
                "hold_float_ratio": _f(row.get("hold_float_ratio")),
                "hold_change": _f(row.get("hold_change")),
                "holder_type": row.get("holder_type"),
            })
        return validated

    # ── Store ───────────────────────────────────────────

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkHolderFloatTop).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec.get("ann_date"),
                    end_date=rec.get("end_date"),
                    holder_name=rec.get("holder_name"),
                ).first()
                if existing:
                    continue
                session.add(RawStkHolderFloatTop(**rec))
                written += 1
        return written

    # ── Run (全市场遍历) ────────────────────────────────

    def run(self, **kwargs) -> dict:
        """全市场遍历拉取，checkpoint 断点续传。"""
        try:
            df = self.pro.stock_basic(exchange="", list_status="L", fields="ts_code")
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception as e:
            logger.error("Failed to get stock list: %s", e)
            return {"status": "failed", "error": str(e), "fetched": 0, "written": 0}

        existing_stocks: set[str] = set()
        try:
            with db_session() as session:
                rows = session.query(RawStkHolderFloatTop.ts_code).distinct().all()
                existing_stocks = {r[0] for r in rows if r[0]}
        except Exception:
            pass

        last_processed = self.get_checkpoint_date() or ""
        start_idx = 0
        if last_processed:
            for i, code in enumerate(all_stocks):
                if code >= last_processed:
                    start_idx = i
                    break

        pending = [s for s in all_stocks[start_idx:] if s not in existing_stocks]

        if not pending:
            logger.info("top10_floatholders: all %d stocks up to date", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("top10_floatholders: %d/%d pending", len(pending), len(all_stocks))

        total_fetched, total_written, total_errors = 0, 0, 0
        t0 = time.time()

        for i, sc in enumerate(pending):
            try:
                raw = self.fetch(ts_code=sc, start_date="20100101", end_date="20261231")
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch(ts_code=sc, start_date="20100101", end_date="20261231")
                else:
                    logger.error("[%d/%d] %s ERROR: %s", i + 1, len(pending), sc, e)
                    total_errors += 1
                    self._update_checkpoint(sc, total_written)
                    continue

            if raw:
                validated = self.validate(raw)
                written = self.store_raw(validated)
                total_fetched += len(raw)
                total_written += written

            self._update_checkpoint(sc, total_written)

            if (i + 1) % 200 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i - 1) / rate if rate > 0 else 0
                logger.info(
                    "[%d/%d] %s +%d rows | %.1f s/s ETA %.0fs",
                    i + 1, len(pending), sc, total_written, rate, eta,
                )

            time.sleep(0.20)

        return {
            "status": "success" if total_errors == 0 else "partial",
            "fetched": total_fetched,
            "written": total_written,
            "errors": total_errors,
        }
