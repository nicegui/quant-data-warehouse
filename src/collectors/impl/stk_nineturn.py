"""神奇九转 — StkNineturnCollector

Tushare stk_nineturn API — TD序列反转指标。
Per-stock API，并行全市场遍历 + checkpoint 断点续传。

数据起始：2023-01-01
频率：daily / 60min
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
import math
from typing import Any

from src.db.session import db_session
from src.models.stk_factor_pro import RawStkNineturn
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


def _clean_signal(v):
    """Normalize nine_up_turn/nine_down_turn: NaN → None, else str."""
    if v is None:
        return None
    try:
        if math.isnan(float(v)):
            return None
    except (ValueError, TypeError):
        pass
    return str(v)


class StkNineturnCollector(BaseTushareCollector):
    """神奇九转 collector — 并行全市场遍历."""

    def __init__(self, token: str, workers: int = 6):
        super().__init__("stk_nineturn", token)
        self.workers = workers

    @property
    def checkpoint_key(self):
        return "ts_code"

    def fetch(self, ts_code: str = "", freq: str = "daily",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {"freq": freq}
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        params.update({k: v for k, v in kwargs.items() if v})
        return self.api_call("stk_nineturn", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": (row.get("trade_date", "") or "").split(" ")[0] if row.get("trade_date") else "",
                "freq": row.get("freq", "daily"),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "close": _f(row.get("close")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "up_count": _f(row.get("up_count")),
                "down_count": _f(row.get("down_count")),
                "nine_up_turn": _clean_signal(row.get("nine_up_turn")),
                "nine_down_turn": _clean_signal(row.get("nine_down_turn")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStkNineturn, records, ["ts_code", "trade_date"])


    def run(self, freq: str = "daily", **kwargs) -> dict:
        """并行全市场遍历，checkpoint 断点续传。

        Args:
            freq: 频率 daily / 60min (默认 daily)
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
            from src.db import nas_duckdb
            result = nas_duckdb.query(f"SELECT DISTINCT ts_code FROM raw_stk_nineturn WHERE freq = '{freq}' AND ts_code IS NOT NULL")
            existing_stocks = {r["ts_code"] for r in result if r.get("ts_code")}
        except Exception:
            try:
                with db_session() as session:
                    rows = session.query(RawStkNineturn.ts_code).filter(
                        RawStkNineturn.freq == freq
                    ).distinct().all()
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
            logger.info("stk_nineturn(%s): all %d stocks up to date", freq, len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("stk_nineturn(%s): %d/%d pending, %d workers",
                    freq, len(pending), len(all_stocks), self.workers)

        # ── Shared state ──
        result_queue: queue.Queue = queue.Queue(maxsize=50)
        lock = threading.Lock()

        stats = {"fetched": 0, "written": 0, "errors": 0, "done": 0}
        t0 = time.time()

        def fetch_one(sc: str):
            """Fetch one stock, push validated rows to queue."""
            time.sleep(0.20)  # serial rate limit
            try:
                raw = self.fetch(ts_code=sc, freq=freq,
                                 start_date="20230101", end_date="20261231")
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch(ts_code=sc, freq=freq,
                                     start_date="20230101", end_date="20261231")
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
