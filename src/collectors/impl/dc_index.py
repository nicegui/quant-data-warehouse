"""大宗商品指数 — DcIndexCollector

Tushare dc_index API — 东方财富概念/行业板块指数行情.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.dc_index import RawDcIndex
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class DcIndexCollector(BaseTushareCollector):
    """大宗商品指数 collector (全量拉取)."""

    def __init__(self, token: str):
        super().__init__("dc_index", token)

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("dc_index", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "name": row.get("name", ""),
                "leading": row.get("leading", ""),
                "leading_code": row.get("leading_code", ""),
                "pct_change": _f(row.get("pct_change")),
                "leading_pct": _f(row.get("leading_pct")),
                "total_mv": _f(row.get("total_mv")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "up_num": row.get("up_num"),
                "down_num": row.get("down_num"),
                "idx_type": row.get("idx_type", ""),
                "level": row.get("level"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawDcIndex).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawDcIndex(**rec))
                written += 1
        return written
