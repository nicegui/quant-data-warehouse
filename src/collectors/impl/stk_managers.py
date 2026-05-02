"""上市公司管理层 — StkManagersCollector

Tushare stk_managers API — 管理层名册（性别/学历/任期等）。
支持逗号多票批量，本 collector 自动遍历全市场股票。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawStkManagers
from src.collectors.base import BaseTushareCollector

logger = logging.getLogger(__name__)

BATCH_SIZE = 20


class StkManagersCollector(BaseTushareCollector):
    """上市公司管理层 collector (全市场遍历)."""

    def __init__(self, token: str):
        super().__init__("stk_managers", token)

    @property
    def checkpoint_key(self) -> str:
        return "ts_code"  # 按股票代码 checkpoint

    def fetch(self, ts_code: str = "", ann_date: str = "", **kw) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("stk_managers", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        fields = (
            "ts_code", "ann_date", "name", "gender", "lev", "title",
            "edu", "national", "birthday", "begin_date", "end_date",
        )
        return [{k: row.get(k) for k in fields} for row in raw]

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkManagers).filter_by(
                    ts_code=rec["ts_code"],
                    name=rec.get("name"),
                    title=rec.get("title"),
                ).first()
                if existing:
                    continue
                session.add(RawStkManagers(**rec))
                written += 1
        return written

    def run(self, **kwargs) -> dict:
        """全市场遍历拉取，支持 checkpoint 断点续传."""
        # 1. 全股票列表
        try:
            df = self.pro.stock_basic(exchange="", list_status="L", fields="ts_code")
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception as e:
            logger.error("Failed to get stock list: %s", e)
            return {"status": "failed", "error": str(e), "fetched": 0, "written": 0}

        # 2. DB 已有股票
        existing_stocks: set[str] = set()
        try:
            with db_session() as session:
                rows = session.query(RawStkManagers.ts_code).distinct().all()
                existing_stocks = {r[0] for r in rows if r[0]}
        except Exception:
            pass

        # 3. Checkpoint
        last_processed = self.get_checkpoint_date() or ""
        start_idx = 0
        if last_processed:
            for i, code in enumerate(all_stocks):
                if code >= last_processed:
                    start_idx = i
                    break

        pending = [s for s in all_stocks[start_idx:] if s not in existing_stocks]

        if not pending:
            logger.info("stk_managers: all %d stocks up to date", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0,
                    "message": f"All {len(all_stocks)} stocks up to date"}

        logger.info("stk_managers: %d/%d stocks need fetching (existing=%d)",
                     len(pending), len(all_stocks), len(existing_stocks))

        total_fetched = 0
        total_written = 0
        total_errors = 0
        total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_no in range(total_batches):
            start = batch_no * BATCH_SIZE
            batch = pending[start : start + BATCH_SIZE]
            codes = ",".join(batch)

            try:
                raw = self._fetch_with_retry(ts_code=codes)
                if not raw:
                    self._update_checkpoint(batch[-1], total_written)
                    continue

                validated = self.validate(raw)
                written = self.store_raw(validated)

                total_fetched += len(raw)
                total_written += written

                logger.info("[%d/%d] %s…%s → fetch=%d write=%d | acc=%d/%d err=%d",
                            batch_no + 1, total_batches,
                            batch[0], batch[-1],
                            len(raw), written,
                            total_fetched, total_written, total_errors)

                self._update_checkpoint(batch[-1], total_written)

            except Exception as e:
                total_errors += 1
                logger.error("[%d/%d] %s…%s ERROR: %s",
                             batch_no + 1, total_batches, batch[0], batch[-1], e)
                self._update_checkpoint(batch[-1], total_written)
                time.sleep(1)

            time.sleep(0.2)

        return {
            "status": "success" if total_errors == 0 else "partial",
            "fetched": total_fetched,
            "written": total_written,
            "errors": total_errors,
            "checkpoint": self.get_checkpoint_date(),
        }
