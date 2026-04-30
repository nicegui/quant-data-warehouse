"""业绩快报 — ExpressCollector

Tushare express API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawExpress
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ExpressCollector(BaseTushareCollector):
    """业绩快报 collector."""

    def __init__(self, token: str):
        super().__init__("express", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, end_date: str = "", ts_code: str = "", ann_date: str = "", **kwargs) -> list[dict]:
        params = {}
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        if ann_date:
            params["ann_date"] = ann_date
        return self.api_call("express", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "revenue": _f(row.get("revenue")),
                "operate_profit": _f(row.get("operate_profit")),
                "total_profit": _f(row.get("total_profit")),
                "n_income": _f(row.get("n_income")),
                "n_income_attr_p": _f(row.get("n_income_attr_p")),
                "total_assets": _f(row.get("total_assets")),
                "paid_assets": _f(row.get("paid_assets")),
                "total_hldr_eqy_exc_min_int": _f(row.get("total_hldr_eqy_exc_min_int")),
                "eps": _f(row.get("eps")),
                "bps": _f(row.get("bps")),
                "weighted_roe": _f(row.get("weighted_roe")),
                "total_revenue_so": _f(row.get("total_revenue_so")),
                "operate_profit_so": _f(row.get("operate_profit_so")),
                "n_income_so": _f(row.get("n_income_so")),
                "n_income_attr_p_so": _f(row.get("n_income_attr_p_so")),
                "update_flag": row.get("update_flag"),
                "yoy_eps": _f(row.get("yoy_eps")),
                "yoy_net_profit": _f(row.get("yoy_net_profit")),
                "grossprofit_margin": _f(row.get("grossprofit_margin")),
                "netprofit_margin": _f(row.get("netprofit_margin")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawExpress).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawExpress(**rec))
                written += 1
        return written
