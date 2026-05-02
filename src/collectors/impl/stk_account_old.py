"""旧版股票开户数 — StkAccountOldCollector

Tushare stk_account_old API — 历史周度开户数据（沪深分市场）。
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.market import RawStkAccountOld
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkAccountOldCollector(BaseTushareCollector):
    """旧版股票开户数 collector (全量拉取, 378条)."""

    def __init__(self, token: str):
        super().__init__("stk_account_old", token)

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("stk_account_old", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "date": row.get("date", ""),
                "new_sh": row.get("new_sh"),
                "new_sz": row.get("new_sz"),
                "active_sh": _f(row.get("active_sh")),
                "active_sz": _f(row.get("active_sz")),
                "total_sh": _f(row.get("total_sh")),
                "total_sz": _f(row.get("total_sz")),
                "trade_sh": _f(row.get("trade_sh")),
                "trade_sz": _f(row.get("trade_sz")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkAccountOld).filter_by(
                    date=rec["date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkAccountOld(**rec))
                written += 1
        return written
