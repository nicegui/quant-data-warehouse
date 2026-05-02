"""中央结算系统持股明细 — CcassHoldDetailCollector

Tushare ccass_hold_detail API: HK CCASS 席位级持股明细。
Per-stock API，月度分块并行遍历全市场。
"""
from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any

from src.models.hk_market import RawCcassHoldDetail
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class CcassHoldDetailCollector(BaseTushareCollector):
    """CCASS 席位持股明细 — 并行全市场遍历."""

    def __init__(self, token: str, workers: int = 5):
        super().__init__("ccass_hold_detail", token)
        self.workers = workers

    @property
    def checkpoint_key(self):
        return "ts_code"

    def fetch(self, ts_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("ccass_hold_detail", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"trade_date", "ts_code", "name",
                      "col_participant_id", "col_participant_name"}
        validated = []
        for row in raw:
            rec = {}
            for k, v in row.items():
                if k == "raw_json":
                    continue
                if k in STR_FIELDS:
                    # Normalize NaN/float IDs to empty string
                    rec[k] = "" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)
                else:
                    rec[k] = _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(
            RawCcassHoldDetail, records,
            ["ts_code", "trade_date", "col_participant_id"],
        )

    # ── Backward-pagination Run ─────────────────────────

    _PAGE_SIZE = 7000  # Tushare API hard limit per call

    def run(self, **kwargs) -> dict:
        """Backward-pagination per stock: fetch 7000-row pages until exhausted.

        Instead of 60 monthly calls per stock (163K total), each stock
        paginates backward through its history in 7000-row chunks.
        Average stock needs 2-4 pages → ~8K calls total → ~30 min.

        Fast-skip: if first page for a stock writes 0 rows (all duplicates),
        mark stock as fully cached in checkpoint and skip remaining pages.
        """
        # ── Get HK stock list ──
        try:
            df = self.pro.hk_basic(list_status="L")
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception:
            try:
                df = self.pro.ccass_hold(trade_date="20260429")
                all_stocks = sorted(df["ts_code"].unique().tolist())
            except Exception as e:
                logger.error("Failed to get stock list: %s", e)
                return {"status": "failed", "error": str(e)}

        # ── Load checkpoint: last trade_date per stock ──
        checkpoint = self._load_date_checkpoint()
        pending = []
        skipped = 0
        for sc in all_stocks:
            last_date = checkpoint.get(sc)
            if last_date and last_date <= "20210601":  # exhausted/cached
                skipped += 1
                continue
            pending.append(sc)

        if not pending:
            logger.info("ccass_hold_detail: all %d stocks up to date (%d cached)",
                       len(all_stocks), skipped)
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("ccass_hold_detail: %d stocks, backward pagination (%d cached, page=%d rows)",
                    len(pending), skipped, self._PAGE_SIZE)

        stats = {"fetched": 0, "written": 0, "errors": 0, "pages": 0, "fast_skipped": 0}
        t0 = time.time()
        n = len(pending)

        for i, sc in enumerate(pending):
            end_date = checkpoint.get(sc)  # None = start from latest
            first_page = True
            while True:
                time.sleep(0.20)
                try:
                    if end_date:
                        raw = self.fetch(ts_code=sc, end_date=end_date)
                    else:
                        raw = self.fetch(ts_code=sc)
                except Exception:
                    stats["errors"] += 1
                    break  # skip to next stock on error

                if not raw:
                    break  # exhausted

                validated = self.validate(raw)
                written = self.store_raw(validated)
                stats["fetched"] += len(validated)
                stats["written"] += written
                stats["pages"] += 1

                # Fast-skip: first page all duplicates → stock fully cached
                if first_page and written == 0:
                    self._save_date_checkpoint(sc, "20210601")  # mark as cached
                    stats["fast_skipped"] += 1
                    break

                first_page = False

                # Next page: earliest date minus 1 day
                min_date = min(r["trade_date"] for r in raw)
                end_date = (datetime.strptime(min_date, "%Y%m%d")
                            - timedelta(days=1)).strftime("%Y%m%d")
                self._save_date_checkpoint(sc, end_date)

                if len(raw) < self._PAGE_SIZE:
                    break  # last page

            # Progress + memory cleanup every 100 stocks
            done = i + 1
            if done % 100 == 0:
                import gc; gc.collect()
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                eta = (n - done) / rate if rate > 0 else 0
                logger.info("[%d/%d] %s pages, %s new, %s skip | %.1f stk/s ETA %.0fs",
                            done, n, f"{stats['pages']:,}",
                            f"{stats['written']:,}", f"{stats['fast_skipped']:,}",
                            rate, eta)

        elapsed = time.time() - t0
        logger.info("ccass_hold_detail DONE: %d stocks, %d pages, %s new, %s skip, %.0fs",
                    n, stats["pages"], f"{stats['written']:,}",
                    f"{stats['fast_skipped']:,}", elapsed)
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "fast_skipped": stats["fast_skipped"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }

    def _load_date_checkpoint(self) -> dict[str, str]:
        """Load per-stock last trade_date from checkpoint file."""
        state = self.checkpoint.load()
        if state and "dates" in state:
            return state["dates"]
        return {}

    def _save_date_checkpoint(self, ts_code: str, end_date: str):
        """Save per-stock cursor after each page."""
        state = self.checkpoint.load() or {}
        if "dates" not in state:
            state["dates"] = {}
        state["dates"][ts_code] = end_date
        self.checkpoint.save(dates=state["dates"])
