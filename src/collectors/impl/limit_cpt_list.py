"""最强板块统计 — LimitCptListCollector

Tushare limit_cpt_list API — 每日涨停最多最强的概念板块排名。
~20 sectors/day, 从 2023 年开始。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawLimitCptList
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class LimitCptListCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("limit_cpt_list", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("limit_cpt_list", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")) if row.get("name") else "",
                "days": int(row["days"]) if row.get("days") is not None else None,
                "up_stat": str(row.get("up_stat", "")) if row.get("up_stat") else "",
                "cons_nums": int(row["cons_nums"]) if row.get("cons_nums") is not None else None,
                "up_nums": int(row["up_nums"]) if row.get("up_nums") is not None else None,
                "pct_chg": _f(row.get("pct_chg")),
                "rank": str(row.get("rank", "")) if row.get("rank") else "",
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawLimitCptList, records, ["trade_date", "ts_code"])

    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query("SELECT DISTINCT trade_date FROM raw_limit_cpt_list")
            return {row[0] for row in result["rows"]}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        existing = self._get_existing_dates()
        d0 = datetime(2023, 1, 1)
        today = datetime.now()
        dp = []
        d = d0
        while d <= today:
            if d.weekday() < 5:
                dp.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)

        last_date = self.get_checkpoint_date()
        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0, "skipped": 0}
        t0 = time.time()

        for d in dp:
            if last_date and d <= last_date:
                stats["skipped"] += 1
                continue
            if d in existing:
                continue
            time.sleep(0.20)
            try:
                raw = self.fetch(trade_date=d)
            except Exception:
                stats["errors"] += 1
                continue
            if not raw:
                continue
            validated = self.validate(raw)
            written = self.store_raw(validated)
            stats["fetched"] += len(validated)
            stats["written"] += written
            stats["days"] += 1
            self._update_checkpoint(d, written)

        elapsed = time.time() - t0
        logger.info("limit_cpt_list DONE: %d days, %s rows, %d skipped, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["skipped"], elapsed)
        return {**stats, "status": "success" if stats["errors"] == 0 else "partial", "elapsed": elapsed}
