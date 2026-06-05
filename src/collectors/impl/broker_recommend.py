"""券商月度荐股 — BrokerRecommendCollector

Tushare broker_recommend API — 券商月度金股推荐。
按月全量获取（单月~250行，远低于1000限制）。
串行遍历，轻量无内存风险。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.events import RefBrokerRecommend
from src.collectors.base import BaseTushareCollector

logger = logging.getLogger(__name__)

# Months from 2010 to 2026
_MONTHS = [f"{y}{m:02d}" for y in range(2010, 2027) for m in range(1, 13)]


class BrokerRecommendCollector(BaseTushareCollector):
    """券商荐股 collector — 按月全量获取."""

    def __init__(self, token: str):
        super().__init__("broker_recommend", token)

    @property
    def checkpoint_key(self) -> str:
        return "month"

    def fetch(self, month: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if month:
            params["month"] = month
        params.update({k: v for k, v in kwargs.items() if v})
        return self.api_call("broker_recommend", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "month": row.get("month", ""),
                "broker": row.get("broker"),
                "ts_code": row.get("ts_code"),
                "name": row.get("name"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefBrokerRecommend, records, ["month", "broker", "ts_code"])


    def run(self, **kwargs) -> dict:
        existing_months: set[str] = set()
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query("SELECT DISTINCT month FROM ref_broker_recommend WHERE month IS NOT NULL AND month != ''")
            existing_months = {str(r["month"]) for r in result if r.get("month")}
        except Exception:
            try:
                with db_session() as session:
                    rows = session.query(RefBrokerRecommend.month).distinct().all()
                    existing_months = {r[0] for r in rows if r[0]}
            except Exception:
                pass

        pending = [m for m in _MONTHS if m not in existing_months]
        if not pending:
            logger.info("broker_recommend: all months up to date")
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("broker_recommend: %d months pending", len(pending))

        total_fetched, total_written, total_errors = 0, 0, 0
        t0 = time.time()

        for i, m in enumerate(pending):
            try:
                raw = self.fetch(month=m)
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch(month=m)
                else:
                    total_errors += 1
                    continue

            if raw:
                validated = self.validate(raw)
                written = self.store_raw(validated)
                total_fetched += len(raw)
                total_written += written

            if (i + 1) % 20 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info("[%d/%d] %s +%d rows | %.1f/s",
                            i + 1, len(pending), m, total_written, rate)

            time.sleep(0.25)

        return {
            "status": "success" if total_errors == 0 else "partial",
            "fetched": total_fetched,
            "written": total_written,
            "errors": total_errors,
        }
