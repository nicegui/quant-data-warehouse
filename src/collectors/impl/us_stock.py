"""美股 — UsStockCollector

Tushare us_daily + us_basic API — 美股日线 + 基本信息.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.us_market import RawUsDaily, RawUsBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class UsStockCollector(BaseTushareCollector):
    """美股 collector (us_daily + us_basic)."""

    FREQ_CONFIG = {
        "us_daily": {
            "api": "us_daily",
            "model": RawUsDaily,
            "label": "us_daily",
        },
        "us_basic": {
            "api": "us_basic",
            "model": RawUsBasic,
            "label": "us_basic",
        },
    }

    def __init__(self, token: str, sub_api: str = "us_daily"):
        if sub_api not in self.FREQ_CONFIG:
            raise ValueError(f"sub_api must be one of {list(self.FREQ_CONFIG)}")
        self.sub_api = sub_api
        cfg = self.FREQ_CONFIG[sub_api]
        super().__init__(cfg["label"], token)
        self._api_name = cfg["api"]
        self._model = cfg["model"]

    @property
    def checkpoint_key(self):
        return "trade_date" if self.sub_api == "us_daily" else None

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        params.update(kwargs)
        return self.api_call(self._api_name, **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            if self.sub_api == "us_daily":
                rec = {
                    "ts_code": row.get("ts_code", ""),
                    "trade_date": row.get("trade_date"),
                    "open": _f(row.get("open"), 0),
                    "high": _f(row.get("high"), 0),
                    "low": _f(row.get("low"), 0),
                    "close": _f(row.get("close"), 0),
                    "pre_close": _f(row.get("pre_close"), 0),
                    "pct_change": _f(row.get("pct_change"), 0),
                    "vol": _f(row.get("vol"), 0),
                    "amount": _f(row.get("amount"), 0),
                    "vwap": _f(row.get("vwap"), 0),
                    "raw_json": json.dumps(row, ensure_ascii=False, default=str),
                }
            else:
                rec = {
                    "ts_code": row.get("ts_code", ""),
                    "name": row.get("name", ""),
                    "enname": row.get("enname", ""),
                    "classify": row.get("classify", ""),
                    "list_date": row.get("list_date"),
                    "delist_date": row.get("delist_date"),
                    "raw_json": json.dumps(row, ensure_ascii=False, default=str),
                }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                q = session.query(self._model).filter_by(
                    ts_code=rec["ts_code"],
                )
                if self.sub_api == "us_daily":
                    q = q.filter_by(trade_date=rec.get("trade_date"))
                existing = q.first()
                if existing:
                    continue
                session.add(self._model(**rec))
                written += 1
        return written
