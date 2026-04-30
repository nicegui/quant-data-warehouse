"""主营业务构成 — FinaMainbzCollector

Tushare fina_mainbz API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawFinaMainbz
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FinaMainbzCollector(BaseTushareCollector):
    """主营业务构成 collector."""

    def __init__(self, token: str):
        super().__init__("fina_mainbz", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", end_date: str = "",
              bz_type: str = "P", **kwargs) -> list[dict]:
        params: dict[str, Any] = {"type": bz_type}
        if not (ts_code or end_date):
            ts_code = "000001.SZ"
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fina_mainbz", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "bz_item": row.get("bz_item", ""),
                "bz_code": row.get("bz_code", ""),
                "bz_sales": _f(row.get("bz_sales")),
                "bz_profit": _f(row.get("bz_profit")),
                "bz_cost": _f(row.get("bz_cost")),
                "curr_type": row.get("curr_type", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinaMainbz).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                    bz_item=rec.get("bz_item"),
                ).first()
                if existing:
                    continue
                session.add(RawFinaMainbz(**rec))
                written += 1
        return written
