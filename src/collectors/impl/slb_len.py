"""转融通融资汇总 — SlbLenCollector

Tushare slb_len API — 转融通融资汇总（日频大盘数据）。

API limit: 5000 rows per call. Date-based historical backfill.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class SlbLenCollector(BaseTushareCollector):
    """转融通融资汇总 collector — 日频拉取."""

    def __init__(self, token: str):
        super().__init__("slb_len", token)

    def fetch(self, trade_date: str = "", start_date: str = "",
              end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("slb_len", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ob": _f(row.get("ob")),
                "auc_amount": _f(row.get("auc_amount")),
                "repo_amount": _f(row.get("repo_amount")),
                "repay_amount": _f(row.get("repay_amount")),
                "cb": _f(row.get("cb")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        from sqlalchemy import text
        from src.models.sentiment import RawSlbLen
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawSlbLen).filter_by(
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawSlbLen(**rec))
                written += 1
        return written

    def run(self, **kwargs) -> dict:
        """Pull full history in year-sized chunks."""
        years = [(y, min(y + 1, datetime.now().year)) for y in range(2010, datetime.now().year + 1)]
        stats = {"fetched": 0, "written": 0, "errors": 0}
        t0 = time.time()

        for y_start, y_end in years:
            sd = f"{y_start}0101"
            ed = f"{y_end}1231" if y_end < datetime.now().year else datetime.now().strftime("%Y%m%d")
            time.sleep(0.20)
            try:
                raw = self.fetch(start_date=sd, end_date=ed)
            except Exception:
                stats["errors"] += 1
                continue
            if not raw:
                continue

            validated = self.validate(raw)
            written = self.store_raw(validated)
            stats["fetched"] += len(validated)
            stats["written"] += written
            logger.info("slb_len %s-%s: %d rows, %d new", sd[:4], ed[:4], len(validated), written)

        elapsed = time.time() - t0
        logger.info("slb_len DONE: %s rows, %.0fs", f"{stats['written']:,}", elapsed)
        return {"status": "success", "fetched": stats["fetched"], "written": stats["written"],
                "errors": stats["errors"], "elapsed": elapsed}
