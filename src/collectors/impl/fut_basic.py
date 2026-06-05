"""期货基本信息 — FutBasicCollector

Tushare fut_basic API — 全量更新，无 checkpoint。
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.futures import RefFutBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FutBasicCollector(BaseTushareCollector):
    """期货基本信息 collector (全量更新)."""

    def __init__(self, token: str):
        super().__init__("fut_basic", token)

    @property
    def checkpoint_key(self):
        return None  # 全量拉取，无需 checkpoint

    def fetch(self, exchange: str = "", fut_type: str = "", **kwargs) -> list[dict]:
        """Fetch futures basic info.

        Args:
            exchange: DCE | CZCE | SHFE | CFFEX | INE (optional, empty = all)
            fut_type: 1=普通合约, 2=主力合约 (optional)
        """
        params: dict[str, Any] = {}
        if exchange:
            params["exchange"] = exchange
        if fut_type:
            params["fut_type"] = fut_type
        return self.api_call("fut_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "symbol": row.get("symbol"),
                "exchange": row.get("exchange"),
                "name": row.get("name"),
                "fut_code": row.get("fut_code"),
                "multiplier": _f(row.get("multiplier")),
                "trade_unit": row.get("trade_unit"),
                "per_unit": _f(row.get("per_unit")),
                "quote_unit": row.get("quote_unit"),
                "quote_unit_desc": row.get("quote_unit_desc"),
                "d_mode_desc": row.get("d_mode_desc"),
                "list_date": row.get("list_date"),
                "delist_date": row.get("delist_date"),
                "d_month": row.get("d_month"),
                "last_ddate": row.get("last_ddate"),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RefFutBasic, records, ["ts_code"])
