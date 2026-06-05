"""指数基本信息 — IndexBasicCollector

Tushare index_basic API — 全量拉取，无 checkpoint。
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.index import RefIndexBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class IndexBasicCollector(BaseTushareCollector):
    """指数基本信息 collector (全量更新)."""

    def __init__(self, token: str):
        super().__init__("index_basic", token)

    @property
    def checkpoint_key(self):
        return None  # 全量拉取，无需 checkpoint

    def fetch(self, market: str = "", **kwargs) -> list[dict]:
        """Fetch index basic info.

        Args:
            market: SSE | SZSE | CICC (optional, empty = all markets)
        """
        params: dict[str, Any] = {}
        if market:
            params["market"] = market
        return self.api_call("index_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name"),
                "market": row.get("market"),
                "publisher": row.get("publisher"),
                "category": row.get("category"),
                "base_date": row.get("base_date"),
                "base_point": _f(row.get("base_point")),
                "list_date": row.get("list_date"),
                "exp_date": row.get("exp_date"),
                "fullname": row.get("fullname"),
                "index_type": row.get("index_type"),
                "weight_rule": row.get("weight_rule"),
                "desc": row.get("desc"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefIndexBasic, records, ["ts_code"])


    def run(self) -> dict:
        """Full fetch: all markets, upsert into ref_index_basic."""
        import logging, time
        logger = logging.getLogger(__name__)
        t0 = time.time()
        total = 0

        markets = ["SSE", "SZSE", "CSI", "CICC", "SW", "MSCI", "OTH"]
        for m in markets:
            raw = self.fetch(market=m)
            if raw:
                validated = self.validate(raw)
                written = self.store_raw(validated)
                total += written
                logger.info(f"[{m}] {written} rows")
            else:
                logger.info(f"[{m}] EMPTY")
            time.sleep(0.21)

        elapsed = time.time() - t0
        logger.info(f"index_basic DONE: {total} rows, {int(elapsed)}s")
        return {"status": "success", "written": total, "elapsed": elapsed}
