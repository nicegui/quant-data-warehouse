"""筹码表现 — CyqPerfCollector

Tushare cyq_perf API — 筹码表现指标 (成本分布、获利比例等).
Per-stock API，支持并行全市场遍历 + checkpoint 断点续传。
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from datetime import date, timedelta
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawCyqPerf
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class CyqPerfCollector(BaseTushareCollector):
    """筹码表现 collector — 并行全市场遍历."""

    def __init__(self, token: str, workers: int = 8):
        super().__init__("cyq_perf", token)
        self.workers = workers

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", trade_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not ts_code and not trade_date:
            params["trade_date"] = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        params.update({k: v for k, v in kwargs.items() if v})
        return self.api_call("cyq_perf", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "his_low": _f(row.get("his_low")),
                "his_high": _f(row.get("his_high")),
                "cost_5pct": _f(row.get("cost_5pct")),
                "cost_15pct": _f(row.get("cost_15pct")),
                "cost_50pct": _f(row.get("cost_50pct")),
                "cost_85pct": _f(row.get("cost_85pct")),
                "cost_95pct": _f(row.get("cost_95pct")),
                "weight_avg": _f(row.get("weight_avg")),
                "winner_rate": _f(row.get("winner_rate")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCyqPerf).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawCyqPerf(**rec))
                written += 1
        return written

    # ── Parallel Run ────────────────────────────────────

    def run(self, **kwargs) -> dict:
        """并行全市场遍历，checkpoint 断点续传。

        多线程并发 fetch，单线程串行 insert 避免 DB 竞争。
        """
        # ── Get stock list ──
        try:
            df = self.pro.stock_basic(exchange="", list_status="L", fields="ts_code")
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception as e:
            logger.error("Failed to get stock list: %s", e)
            return {"status": "failed", "error": str(e), "fetched": 0, "written": 0}

        # ── Compute pending ──
        existing_stocks: set[str] = set()
        try:
            with db_session() as session:
                rows = session.query(RawCyqPerf.ts_code).distinct().all()
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
            logger.info("cyq_perf: all %d stocks up to date", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("cyq_perf: %d/%d pending, %d workers", len(pending), len(all_stocks), self.workers)

        # ── Shared state ──
        result_queue: queue.Queue = queue.Queue(maxsize=50)
        lock = threading.Lock()

        stats = {"fetched": 0, "written": 0, "errors": 0, "done": 0}
        t0 = time.time()

        def fetch_one(sc: str):
            """Fetch one stock, push validated rows to queue."""
            time.sleep(0.20)  # serial rate limit
            try:
                raw = self.fetch(ts_code=sc, start_date="20180101", end_date="20261231")
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch(ts_code=sc, start_date="20180101", end_date="20261231")
                else:
                    with lock:
                        stats["errors"] += 1
                    return

            if raw:
                validated = self.validate(raw)
                result_queue.put((sc, validated))

        # ── Inserter thread ──
        def inserter():
            while True:
                item = result_queue.get()
                if item is None:  # poison pill
                    break
                sc, rows = item
                written = self.store_raw(rows)
                with lock:
                    stats["written"] += written
                    stats["fetched"] += len(rows)
                    stats["done"] += 1
                    done = stats["done"]
                    self._update_checkpoint(sc, stats["written"])

                if done % 200 == 0:
                    elapsed = time.time() - t0
                    with lock:
                        w = stats["written"]
                    rate = done / elapsed if elapsed > 0 else 0
                    eta = (len(pending) - done) / rate if rate > 0 else 0
                    logger.info("[%d/%d] %s +%d rows | %.1f s/s ETA %.0fs",
                                done, len(pending), sc, w, rate, eta)

                result_queue.task_done()

        ins_thread = threading.Thread(target=inserter, daemon=True)
        ins_thread.start()

        # ── Serial fetch ──
        for sc in pending:
            fetch_one(sc)

        # Signal inserter to stop
        result_queue.put(None)
        ins_thread.join(timeout=30)

        elapsed = time.time() - t0
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
