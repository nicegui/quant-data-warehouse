"""备用列表 — BakBasicCollector

Tushare bak_basic API — 备用列表基础信息.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.reference import RawBakBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class BakBasicCollector(BaseTushareCollector):
    """备用列表 collector (全量拉取)."""

    def __init__(self, token: str):
        super().__init__("bak_basic", token)

    def fetch(self, **kwargs) -> list[dict]:
        return self.api_call("bak_basic", **kwargs)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date", ""),
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name", ""),
                "industry": row.get("industry", ""),
                "area": row.get("area", ""),
                "pe": _f(row.get("pe")),
                "float_share": _f(row.get("float_share")),
                "total_share": _f(row.get("total_share")),
                "total_assets": _f(row.get("total_assets")),
                "liquid_assets": _f(row.get("liquid_assets")),
                "fixed_assets": _f(row.get("fixed_assets")),
                "reserved": _f(row.get("reserved")),
                "reserved_pershare": _f(row.get("reserved_pershare")),
                "eps": _f(row.get("eps")),
                "bvps": _f(row.get("bvps")),
                "pb": _f(row.get("pb")),
                "list_date": row.get("list_date", ""),
                "undp": _f(row.get("undp")),
                "per_undp": _f(row.get("per_undp")),
                "rev_yoy": _f(row.get("rev_yoy")),
                "profit_yoy": _f(row.get("profit_yoy")),
                "gpr": _f(row.get("gpr")),
                "npr": _f(row.get("npr")),
                "holder_num": row.get("holder_num"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawBakBasic).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawBakBasic(**rec))
                written += 1
        return written
