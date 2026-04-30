"""融资融券总量 — MarginTotalCollector

Tushare margin API — 融资融券大盘总量 (margin, 非 margin_detail).
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMarginTotal
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class MarginTotalCollector(BaseTushareCollector):
    """融资融券总量 collector (大盘汇总, 非个股明细).

    API: pro.margin(trade_date=...)
    Fields: trade_date, rzye, rzmre, rzche, rqye, rqmcl, rzrqye
    区别于 MarginCollector (margin_detail) — 那个是个股明细.
    """

    def __init__(self, token: str):
        super().__init__("margin_total", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("margin", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "rzye": _f(row.get("rzye"), 0),
                "rzmre": _f(row.get("rzmre"), 0),
                "rzche": _f(row.get("rzche"), 0),
                "rqye": _f(row.get("rqye"), 0),
                "rqmcl": _f(row.get("rqmcl"), 0),
                "rzrqye": _f(row.get("rzrqye"), 0),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMarginTotal).filter_by(
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawMarginTotal(**rec))
                written += 1
        return written
