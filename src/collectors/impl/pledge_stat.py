"""质押统计 — PledgeStatCollector

Tushare pledge_stat API — 股票质押统计数据。
Per-stock API，本 collector 自动遍历全市场股票，支持 checkpoint 断点续传。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawPledgeStat
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class PledgeStatCollector(BaseTushareCollector):
    """质押统计 collector — 全市场遍历 + checkpoint 断点续传。"""

    def __init__(self, token: str):
        super().__init__("pledge_stat", token)

    @property
    def checkpoint_key(self) -> str:
        return "ts_code"

    # ── Fetch ───────────────────────────────────────────

    def fetch(self, ts_code: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("pledge_stat", **params)

    # ── Validate ────────────────────────────────────────

    def validate(self, raw: list[dict]) -> list[dict]:
        import math
        validated = []
        for row in raw:
            def _i(v):
                """Safe integer — coerce NaN/float to int or None."""
                if v is None:
                    return None
                if isinstance(v, float) and math.isnan(v):
                    return None
                try:
                    return int(float(v))
                except (ValueError, TypeError):
                    return None
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "pledge_count": _i(row.get("pledge_count")),
                "unrest_pledge": _f(row.get("unrest_pledge")),
                "rest_pledge": _f(row.get("rest_pledge")),
                "total_share": _f(row.get("total_share")),
                "pledge_ratio": _f(row.get("pledge_ratio")),
            })
        return validated

    # ── Store ───────────────────────────────────────────

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawPledgeStat).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec.get("end_date"),
                ).first()
                if existing:
                    continue
                session.add(RawPledgeStat(**rec))
                written += 1
        return written

    # ── Run (全市场遍历) ────────────────────────────────

    def run(self, **kwargs) -> dict:
        """全市场遍历拉取，checkpoint 断点续传。

        每只票一次 API 调用，返回该票所有历史周度质押数据。
        """
        try:
            df = self.pro.stock_basic(exchange="", list_status="L", fields="ts_code")
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception as e:
            logger.error("Failed to get stock list: %s", e)
            return {"status": "failed", "error": str(e), "fetched": 0, "written": 0}

        existing_stocks: set[str] = set()
        try:
            with db_session() as session:
                rows = session.query(RawPledgeStat.ts_code).distinct().all()
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
            logger.info("pledge_stat: all %d stocks up to date", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("pledge_stat: %d/%d pending", len(pending), len(all_stocks))

        total_fetched, total_written, total_errors = 0, 0, 0
        t0 = time.time()

        for i, sc in enumerate(pending):
            try:
                raw = self.fetch(ts_code=sc)
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch(ts_code=sc)
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
