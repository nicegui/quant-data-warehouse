"""管理层薪酬与持股 — StkRewardsCollector

Tushare stk_rewards API — 管理层薪酬和持股。
API 要求 ts_code（支持逗号多票），限量 4000 行/次。
本 collector 自动遍历全市场股票，分批拉取，支持 checkpoint 断点续传。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawStkRewards
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)

# 每批股票数（控制在 4000 行限量内；大票约 3500 行/只，小票几十行）
BATCH_SIZE = 20


class StkRewardsCollector(BaseTushareCollector):
    """管理层薪酬与持股 collector.

    全市场遍历模式：获取所有上市股票代码，分批调用 stk_rewards API，
    使用 ts_code 作为 checkpoint 键实现断点续传。
    """

    def __init__(self, token: str):
        super().__init__("stk_rewards", token)

    @property
    def checkpoint_key(self) -> str:
        return "ts_code"

    # ── API fetch ──────────────────────────────────────

    def fetch(self, ts_code: str = "", end_date: str = "", **kw) -> list[dict]:
        """调用 stk_rewards API.

        ts_code: 逗号分隔多个股票代码
        end_date: 报告期
        """
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("stk_rewards", **params)

    # ── Validate ───────────────────────────────────────

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "name": row.get("name", ""),
                "title": row.get("title", ""),
                "reward": _f(row.get("reward")),
                "hold_vol": _f(row.get("hold_vol")),
            })
        return validated

    # ── Store ──────────────────────────────────────────
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStkRewards, records, ["ts_code", "ann_date", "name"])


    def run(self, end_date: str = "", **kwargs) -> dict:
        """全市场遍历拉取，支持 checkpoint 断点续传。

        增量模式：从上次断点的 ts_code 继续，跳过已处理股票。
        """
        # 1. 获取全股票列表
        try:
            df = self.pro.stock_basic(
                exchange="", list_status="L", fields="ts_code"
            )
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception as e:
            logger.error("Failed to get stock list: %s", e)
            return {"status": "failed", "error": str(e), "fetched": 0, "written": 0}

        # 2. 获取 DB 中已有的股票（去重）
        existing_stocks: set[str] = set()
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query("SELECT DISTINCT ts_code FROM raw_stk_rewards WHERE ts_code IS NOT NULL")
            existing_stocks = {r["ts_code"] for r in result if r.get("ts_code")}
        except Exception:
            try:
                with db_session() as session:
                    rows = session.query(RawStkRewards.ts_code).distinct().all()
                    existing_stocks = {r[0] for r in rows if r[0]}
            except Exception:
                pass

        # 3. 确定从哪里开始（checkpoint 或从头）
        last_processed = self.get_checkpoint_date() or ""
        start_idx = 0
        if last_processed:
            for i, code in enumerate(all_stocks):
                if code >= last_processed:
                    start_idx = i
                    break

        pending = [s for s in all_stocks[start_idx:] if s not in existing_stocks]

        if not pending:
            logger.info("stk_rewards: all stocks up to date (%d total)", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0,
                    "message": f"All {len(all_stocks)} stocks up to date"}

        logger.info("stk_rewards: %d/%d stocks need fetching (existing=%d)",
                     len(pending), len(all_stocks), len(existing_stocks))

        # 4. 分批拉取
        total_fetched = 0
        total_written = 0
        total_errors = 0
        total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_no in range(total_batches):
            start = batch_no * BATCH_SIZE
            batch = pending[start : start + BATCH_SIZE]
            codes = ",".join(batch)

            try:
                raw = self._fetch_with_retry(ts_code=codes, end_date=end_date)
                if not raw:
                    # 空结果也记 checkpoint，跳过这批
                    self._update_checkpoint(batch[-1], total_written)
                    continue

                validated = self.validate(raw)
                written = self.store_raw(validated)

                total_fetched += len(raw)
                total_written += written

                logger.info(
                    "[%d/%d] %s…%s → fetch=%d write=%d | acc=%d/%d err=%d",
                    batch_no + 1, total_batches,
                    batch[0], batch[-1],
                    len(raw), written,
                    total_fetched, total_written, total_errors,
                )

                # 每批成功后保存 checkpoint
                self._update_checkpoint(batch[-1], total_written)

            except Exception as e:
                total_errors += 1
                logger.error(
                    "[%d/%d] %s…%s ERROR: %s",
                    batch_no + 1, total_batches, batch[0], batch[-1], e,
                )
                # 出错也记 checkpoint，避免死循环
                self._update_checkpoint(batch[-1], total_written)
                time.sleep(1)

            # API 限速
            time.sleep(0.2)

        return {
            "status": "success" if total_errors == 0 else "partial",
            "fetched": total_fetched,
            "written": total_written,
            "errors": total_errors,
            "checkpoint": self.get_checkpoint_date(),
        }
