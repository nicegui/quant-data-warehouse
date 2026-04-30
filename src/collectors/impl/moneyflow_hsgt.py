"""北向资金 — MoneyflowHsgtCollector

Tushare moneyflow_hsgt API — 沪深港通资金流向 (北向/南向资金).
"""

from __future__ import annotations

from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.moneyflow import RawMoneyflowHsgt
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class MoneyflowHsgtCollector(BaseTushareCollector):
    """北向资金 collector.

    API: pro.moneyflow_hsgt(trade_date=..., start_date=..., end_date=...)
    Fields: trade_date, ggt_ss, ggt_sz, hgt, sgt, north_money, south_money
    """

    def __init__(self, token: str):
        super().__init__("moneyflow_hsgt", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params: dict[str, Any] = {"trade_date": td}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("moneyflow_hsgt", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ggt_ss": _f(row.get("ggt_ss")),
                "ggt_sz": _f(row.get("ggt_sz")),
                "hgt": _f(row.get("hgt")),
                "sgt": _f(row.get("sgt")),
                "north_money": _f(row.get("north_money")),
                "south_money": _f(row.get("south_money")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMoneyflowHsgt).filter_by(
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawMoneyflowHsgt(**rec))
                written += 1
        return written
