"""高管增减持 & 十大股东 — HolderCollector

Tushare stk_holdertrade + top10_holders API
两个 API 共用一个 collector，通过 sub_api 参数区分.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawStkHolderTrade, RawStkHolderTop
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class HolderCollector(BaseTushareCollector):
    """高管增减持 & 十大股东 collector.

    Supports:
      - 'stk_holdertrade' — 董监高持股变动
      - 'stk_holder_top'   — 前十大股东
    """

    FREQ_CONFIG = {
        "stk_holdertrade": {
            "api": "stk_holdertrade",
            "model": RawStkHolderTrade,
            "label": "holder_trade",
            "has_end_date": False,
        },
        "stk_holder_top": {
            "api": "top10_holders",
            "model": RawStkHolderTop,
            "label": "holder_top",
            "has_end_date": True,
        },
    }

    def __init__(self, token: str, sub_api: str = "stk_holdertrade"):
        if sub_api not in self.FREQ_CONFIG:
            raise ValueError(f"sub_api must be one of {list(self.FREQ_CONFIG)}, got {sub_api!r}")
        self.sub_api = sub_api
        cfg = self.FREQ_CONFIG[sub_api]
        super().__init__(cfg["label"], token)
        self._api_name = cfg["api"]
        self._model = cfg["model"]
        self._has_end_date = cfg["has_end_date"]

    @property
    def checkpoint_key(self):
        return "end_date" if self._has_end_date else None

    def fetch(self, ts_code: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        params.update(kwargs)
        return self.api_call(self._api_name, **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec: dict[str, Any]
            if self.sub_api == "stk_holdertrade":
                rec = {
                    "ts_code": row.get("ts_code", ""),
                    "ann_date": row.get("ann_date"),
                    "holder_name": row.get("holder_name"),
                    "holder_type": row.get("holder_type"),
                    "in_de": row.get("in_de"),
                    "change_vol": _f(row.get("change_vol")),
                    "change_ratio": _f(row.get("change_ratio")),
                    "after_share": _f(row.get("after_share")),
                    "after_ratio": _f(row.get("after_ratio")),
                    "avg_price": _f(row.get("avg_price")),
                    "total_share": _f(row.get("total_share")),
                    "raw_json": json.dumps(row, ensure_ascii=False, default=str),
                }
            else:  # stk_holder_top
                rec = {
                    "ts_code": row.get("ts_code", ""),
                    "ann_date": row.get("ann_date"),
                    "end_date": row.get("end_date"),
                    "holder_name": row.get("holder_name"),
                    "hold_amount": _f(row.get("hold_amount")),
                    "hold_ratio": _f(row.get("hold_ratio")),
                    "hold_float_ratio": _f(row.get("hold_float_ratio")),
                    "hold_change": _f(row.get("hold_change")),
                    "holder_type": row.get("holder_type"),
                    "raw_json": json.dumps(row, ensure_ascii=False, default=str),
                }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        keys = ["ts_code", "holder_name"]
        if self._has_end_date:
            keys.append("end_date")
        return self._store_dedup(self._model, records, keys)
