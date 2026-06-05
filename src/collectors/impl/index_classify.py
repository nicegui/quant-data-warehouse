"""申万行业分类 — IndexClassifyCollector

Tushare index_classify API — SW2021行业分类.
"""
from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RefIndexClassify
from src.collectors.base import BaseTushareCollector


class IndexClassifyCollector(BaseTushareCollector):
    """申万行业分类 collector — 全量更新."""

    def __init__(self, token: str):
        super().__init__("index_classify", token)

    def fetch(self, level: str = "L1", src: str = "SW2021", **kwargs) -> list[dict]:
        return self.api_call("index_classify", level=level, src=src)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "index_code": row.get("index_code", ""),
                "industry_name": row.get("industry_name", ""),
                "level": row.get("level", ""),
                "industry_code": row.get("industry_code", ""),
                "is_pub": row.get("is_pub"),
                "parent_code": row.get("parent_code"),
                "src": row.get("src"),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefIndexClassify, records, ["index_code"])


    def run(self) -> dict:
        import time, logging
        logger = logging.getLogger(__name__)
        t0 = time.time(); total = 0
        for level in ("L1","L2","L3"):
            raw = self.fetch(level=level)
            if raw:
                n = self.store_raw(self.validate(raw))
                total += n
                logger.info(f"[{level}] {n} rows")
            time.sleep(0.21)
        logger.info(f"index_classify DONE: {total} rows, {int(time.time()-t0)}s")
        return {"status":"success","written":total,"elapsed":time.time()-t0}
