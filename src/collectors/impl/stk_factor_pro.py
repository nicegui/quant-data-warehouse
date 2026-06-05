"""股票技术面因子(专业版) — StkFactorProCollector

Tushare stk_factor_pro API: 每日技术面因子数据（261列），覆盖全历史。
支持并行日期回填 + checkpoint 断点续传。
"""

from __future__ import annotations

import gc
import json
import logging
import time
from typing import Any

from sqlalchemy import text

from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f
from src.config.settings import settings
from src.db.session import db_session

logger = logging.getLogger(__name__)

TABLE = "raw_stk_factor_pro"
COLUMNS: list[str] | None = None


class StkFactorProCollector(BaseTushareCollector):
    """股票技术面因子(专业版) 采集器 — 并行全量回填."""

    def __init__(self, token: str, workers: int = 8):
        super().__init__("stk_factor_pro", token)
        self.workers = workers

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("stk_factor_pro", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"ts_code", "trade_date"}
        validated = []
        for row in raw:
            rec = {}
            for k, v in row.items():
                if k == "raw_json":
                    continue
                rec[k] = v if k in STR_FIELDS else _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Store validated records — delegates to _insert_batch."""
        if not records:
            return 0
        with db_session() as session:
            n = self._insert_batch(session, records)
        return n

    def _insert_batch(self, session, rows: list[dict]) -> int:
        """Bulk INSERT OR IGNORE / ON CONFLICT per backend."""
        global COLUMNS
        if not rows:
            return 0
        if COLUMNS is None:
            COLUMNS = [k for k in rows[0].keys()]

        cols_str = ", ".join(f'"{c}"' for c in COLUMNS)
        placeholders = ", ".join(":" + c for c in COLUMNS)

        if settings.db_backend == "duckdb":
            sql = text(
                f"INSERT OR IGNORE INTO {TABLE} ({cols_str}) "
                f"VALUES ({placeholders})"
            )
        else:
            sql = text(
                f"INSERT INTO {TABLE} ({cols_str}) "
                f"VALUES ({placeholders}) "
                f"ON CONFLICT (ts_code, trade_date) DO NOTHING"
            )

        session.execute(sql, rows)
        return len(rows)

    # ── Parallel Run ────────────────────────────────────

    def run(self, **kwargs) -> dict:
        """并行日期回填，checkpoint 断点续传。

        多线程并发 fetch，单线程 SQLAlchemy 批量写入。
        """
        # ── Get dates ──
        try:
            cal = self.pro.trade_cal(exchange="SSE", start_date="20180101",
                                     end_date="20260501", is_open="1")
            all_dates = sorted(cal["cal_date"].tolist())
        except Exception as e:
            logger.error("Failed to get trade calendar: %s", e)
            return {"status": "failed", "error": str(e)}

        # ── Skip already-covered dates ──
        done_dates: set[str] = set()
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query(
                f"SELECT trade_date, count(*) as cnt FROM {TABLE} "
                f"GROUP BY trade_date HAVING cnt >= 3000"
            )
            done_dates = {str(r["trade_date"]) for r in result if r.get("trade_date")}
        except Exception:
            try:
                with db_session() as session:
                    result = session.execute(
                        text(f"SELECT trade_date, count(*) FROM {TABLE} "
                             f"GROUP BY trade_date HAVING count(*) >= 3000")
                    )
                    done_dates = {str(r[0]) for r in result.fetchall()}
            except Exception:
                pass

        pending = [d for d in all_dates if d not in done_dates]
        if not pending:
            logger.info("stk_factor_pro: all %d dates up to date", len(all_dates))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("stk_factor_pro: %d/%d dates pending, %d workers",
                    len(pending), len(all_dates), self.workers)

        # ── Serial fetch + direct write ──
        stats = {"fetched": 0, "written": 0, "errors": 0}
        t0 = time.time()

        with db_session() as session:
            for i, trade_date in enumerate(pending):
                time.sleep(0.20)
                try:
                    raw = self.fetch(trade_date=trade_date)
                except Exception as e:
                    stats["errors"] += 1
                    if stats["errors"] <= 3:
                        logger.error("FETCH [%s]: %s", trade_date, e)
                    continue
                if raw:
                    validated = self.validate(raw)
                    # Write in chunks — avoids giant 5000×261 SQL string
                    n = 0
                    for j in range(0, len(validated), 500):
                        n += self._insert_batch(session, validated[j:j+500])
                    stats["written"] += n
                    stats["fetched"] += len(validated)
                    del raw, validated
                    gc.collect()

                done = i + 1
                if done % 100 == 0:
                    elapsed = time.time() - t0
                    rate = done / elapsed if elapsed > 0 else 0
                    eta = (len(pending) - done) / rate if rate > 0 else 0
                    logger.info("[%d/%d] written=%s rate=%.1fd/s ETA=%.0fs",
                                done, len(pending), f"{stats['written']:,}", rate, eta)

        elapsed = time.time() - t0
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
