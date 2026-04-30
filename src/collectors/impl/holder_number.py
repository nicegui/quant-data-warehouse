"""股东户数 — StkHolderNumberCollector

Tushare stk_holdernumber API — 股东户数统计.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.market import RawStkHolderNumber
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkHolderNumberCollector(BaseTushareCollector):
    """股东户数 collector.

    API: pro.stk_holdernumber(ts_code=..., end_date=...)
    Fields: ts_code, ann_date, end_date, holder_num, holder_num_ratio
    """

    def __init__(self, token: str):
        super().__init__("holder_number", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, end_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        ed = end_date or dt.now().strftime("%Y%m%d")
        params: dict[str, Any] = {"end_date": ed}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("stk_holdernumber", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "holder_num": _f(row.get("holder_num")),
                "holder_num_ratio": _f(row.get("holder_num_ratio")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkHolderNumber).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkHolderNumber(**rec))
                written += 1
        return written
