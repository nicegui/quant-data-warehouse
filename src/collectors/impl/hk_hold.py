"""沪深港股通持股明细 — HkHoldCollector

Tushare hk_hold API: 沪深港股通持股明细（南向为主，北向2024年8月已停）。
Date-based bulk API，单日 <3800 条，支持并行全量回填。
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Any

from src.db.session import db_session
from src.models.hk_market import RawHkHold
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class HkHoldCollector(BaseTushareCollector):
    """沪深港股通持股明细 — 并行日期回填."""

    def __init__(self, token: str, workers: int = 6):
        super().__init__("hk_hold", token)
        self.workers = workers

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", exchange: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if exchange:
            params["exchange"] = exchange
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("hk_hold", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"code", "trade_date", "ts_code", "name", "exchange"}
        INT_FIELDS = {"vol"}
        validated = []
        for row in raw:
            rec = {}
            for k, v in row.items():
                if k == "raw_json":
                    continue
                if k in INT_FIELDS:
                    try:
                        rec[k] = int(float(v))
                    except (ValueError, TypeError, AttributeError):
                        rec[k] = None
                elif k in STR_FIELDS:
                    rec[k] = v
                else:
                    rec[k] = _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(
            RawHkHold, records,
            ["ts_code", "trade_date", "exchange"],
        )

    # ── Parallel Run ────────────────────────────────────

    def run(self, **kwargs) -> dict:
        """并行日期回填，checkpoint 断点续传。"""
        try:
            cal = self.pro.trade_cal(exchange="SSE", start_date="20170101",
                                     end_date="20260501", is_open="1")
            all_dates = sorted(cal["cal_date"].tolist())
        except Exception as e:
            logger.error("Failed to get trade calendar: %s", e)
            return {"status": "failed", "error": str(e)}

        # Skip dates already in DB
        existing_dates: set[str] = set()
        try:
            with db_session() as session:
                rows = session.query(RawHkHold.trade_date).distinct().all()
                existing_dates = {str(r[0]) for r in rows if r[0]}
        except Exception:
            pass

        pending = [d for d in all_dates if d not in existing_dates]
        if not pending:
            logger.info("hk_hold: all %d dates up to date", len(all_dates))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("hk_hold: %d/%d dates pending, %d workers",
                    len(pending), len(all_dates), self.workers)

        result_queue: queue.Queue = queue.Queue(maxsize=50)
        lock = threading.Lock()
        stats = {"fetched": 0, "written": 0, "errors": 0, "done": 0}
        t0 = time.time()

        def fetch_one(trade_date: str):
            time.sleep(0.20)  # serial rate limit
            try:
                raw = self.fetch(trade_date=trade_date)
            except Exception as e:
                with lock:
                    stats["errors"] += 1
                return
            if raw:
                result_queue.put((trade_date, self.validate(raw)))

        def inserter():
            while True:
                item = result_queue.get()
                if item is None:
                    break
                _, rows = item
                n = self.store_raw(rows)
                with lock:
                    stats["fetched"] += len(rows)
                    stats["written"] += n
                    stats["done"] += 1
                result_queue.task_done()

        ins_thread = threading.Thread(target=inserter, daemon=True)
        ins_thread.start()

        for i, d in enumerate(pending):
            fetch_one(d)
            if (i + 1) % 100 == 0:
                elapsed = time.time() - t0
                with lock:
                    dd, w = stats["done"], stats["written"]
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i - 1) / rate if rate > 0 else 0
                logger.info("[%d/%d] written=%s | %.1fd/s ETA %.0fs",
                            i + 1, len(pending), f"{w:,}", rate, eta)

        result_queue.put(None)
        ins_thread.join(timeout=60)

        elapsed = time.time() - t0
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
