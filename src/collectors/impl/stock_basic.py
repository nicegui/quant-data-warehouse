"""股票基本信息 — StockBasicCollector

Stock master data (全量更新，每周一次).
"""

from __future__ import annotations

from typing import Any

import uuid
from datetime import datetime, timezone

from src.db.session import db_session
from src.models.reference import RefStockBasic
from src.models.asset import Asset
from src.collectors.base import BaseTushareCollector


class StockBasicCollector(BaseTushareCollector):
    """Stock master data collector."""

    def __init__(self, token: str):
        super().__init__("stock_basic", token)

    # All fields from stock_basic API
    _ALL_FIELDS = (
        "ts_code,symbol,name,area,industry,market,exchange,list_status,"
        "list_date,delist_date,is_hs,act_name,act_ent_type,"
        "fullname,enname,cnspell,curr_type"
    )

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        kwargs.setdefault("fields", self._ALL_FIELDS)
        return self.api_call("stock_basic", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
                "area": row.get("area"),
                "industry": row.get("industry"),
                "market": row.get("market"),
                "exchange": row.get("exchange"),
                "list_status": row.get("list_status"),
                "list_date": row.get("list_date"),
                "delist_date": row.get("delist_date"),
                "is_hs": row.get("is_hs"),
                "act_name": row.get("act_name"),
                "act_ent_type": row.get("act_ent_type"),
                "fullname": row.get("fullname"),
                "enname": row.get("enname"),
                "cnspell": row.get("cnspell"),
                "curr_type": row.get("curr_type"),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Replace stock basic reference data and sync asset registry."""
        written = 0
        now = datetime.now(timezone.utc)
        with db_session() as session:
            # Clear old data
            session.query(RefStockBasic).delete()

            for rec in records:
                ts_code = rec["ts_code"]
                symbol = rec["symbol"]
                name = rec["name"]

                # Upsert asset record
                existing_asset = session.query(Asset).filter(
                    Asset.source_id == ts_code,
                    Asset.asset_type == "stock",
                ).first()

                if existing_asset:
                    asset_id = existing_asset.id
                    existing_asset.name = name
                    existing_asset.symbol = symbol
                else:
                    asset_id = uuid.uuid4()
                    session.add(Asset(
                        id=asset_id,
                        symbol=symbol,
                        exchange="SSE" if ts_code.endswith(".SH") else "SZSE",
                        asset_type="stock",
                        name=name,
                        source_id=ts_code,
                        status="active",
                        valid_from=now,
                        valid_to=None,
                    ))

                # Insert stock basic with asset_id
                list_date = rec.get("list_date")
                if list_date:
                    list_date = datetime.strptime(str(list_date)[:10], "%Y%m%d").replace(tzinfo=timezone.utc)
                delist_date = rec.get("delist_date")
                if delist_date:
                    delist_date = datetime.strptime(str(delist_date)[:10], "%Y%m%d").replace(tzinfo=timezone.utc)

                session.add(RefStockBasic(
                    asset_id=asset_id,
                    ts_code=ts_code,
                    symbol=symbol,
                    name=name,
                    area=rec.get("area"),
                    industry=rec.get("industry"),
                    market=rec.get("market"),
                    exchange=rec.get("exchange"),
                    list_status=rec.get("list_status"),
                    list_date=list_date,
                    delist_date=delist_date,
                    is_hs=rec.get("is_hs"),
                    act_name=rec.get("act_name"),
                    act_ent_type=rec.get("act_ent_type"),
                    fullname=rec.get("fullname"),
                    enname=rec.get("enname"),
                    cnspell=rec.get("cnspell"),
                    curr_type=rec.get("curr_type"),
                ))
                written += 1
        return written
