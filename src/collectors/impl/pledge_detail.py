"""股权质押明细 — PledgeDetailCollector

Tushare pledge_detail API — 股东股权质押明细。
Per-stock API（ts_code 必填），自动遍历全市场，checkpoint 断点续传。
"""
from __future__ import annotations

import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawPledgeDetail
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class PledgeDetailCollector(BaseTushareCollector):
    """股权质押明细 collector — 全市场遍历 + checkpoint 断点续传。"""

    def __init__(self, token: str):
        super().__init__("pledge_detail", token)

    @property
    def checkpoint_key(self) -> str:
        return "ts_code"

    # ── Fetch ───────────────────────────────────────────

    def fetch(self, ts_code: str = "", start_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (ts_code or start_date or end_date):
            ts_code = "000001.SZ"
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("pledge_detail", **params)

    # ── Validate ────────────────────────────────────────

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "holder_name": row.get("holder_name", ""),
                "pledge_amount": _f(row.get("pledge_amount")),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "is_release": row.get("is_release"),
                "release_date": row.get("release_date"),
                "pledgor": row.get("pledgor"),
                "holding_amount": _f(row.get("holding_amount")),
                "pledged_amount": _f(row.get("pledged_amount")),
                "p_total_ratio": _f(row.get("p_total_ratio")),
                "h_total_ratio": _f(row.get("h_total_ratio")),
                "is_buyback": row.get("is_buyback"),
            })
        return validated

    # ── Store ───────────────────────────────────────────

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawPledgeDetail).filter_by(
                    ts_code=rec["ts_code"],
                    ann_date=rec["ann_date"],
                    holder_name=rec["holder_name"],
                ).first()
                if existing:
                    continue
                session.add(RawPledgeDetail(**rec))
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
                rows = session.query(RawPledgeDetail.ts_code).distinct().all()
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
            logger.info("pledge_detail: all %d stocks up to date", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("pledge_detail: %d/%d pending", len(pending), len(all_stocks))

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
