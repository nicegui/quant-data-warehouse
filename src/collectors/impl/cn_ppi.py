"""工业品出厂价格指数 PPI — CnPpiCollector

Tushare cn_ppi API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.macro import RawCnPpi
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CnPpiCollector(BaseTushareCollector):
    """PPI 工业品出厂价格指数 collector."""

    def __init__(self, token: str):
        super().__init__("cn_ppi", token)

    @property
    def checkpoint_key(self):
        return "month"

    def fetch(self, month: str = "", start_period: str = "", end_period: str = "", **kwargs) -> list[dict]:
        """Fetch PPI data.

        Args:
            month: YYYYMM (single month, for checkpoint resume)
            start_period: YYYYMM
            end_period: YYYYMM
        """
        params: dict[str, Any] = {}
        if month:
            # Checkpoint provides month in the checkpoint_key param;
            # use it as start_period to resume from last known month
            params["start_period"] = month
        if start_period:
            params["start_period"] = start_period
        if end_period:
            params["end_period"] = end_period
        return self.api_call("cn_ppi", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "month": row.get("month"),
                "ppi_yoy": _f(row.get("ppi_yoy")),
                "ppi_mp_yoy": _f(row.get("ppi_mp_yoy")),
                "ppi_rm_yoy": _f(row.get("ppi_rm_yoy")),
                "ppi_living_yoy": _f(row.get("ppi_living_yoy")),
                "ppi_cg_yoy": _f(row.get("ppi_cg_yoy")),
                "ppi_mp_mom": _f(row.get("ppi_mp_mom")),
                "ppi_rm_mom": _f(row.get("ppi_rm_mom")),
                "ppi_living_mom": _f(row.get("ppi_living_mom")),
                "ppi_cg_mom": _f(row.get("ppi_cg_mom")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnPpi).filter_by(
                    month=rec["month"],
                ).first()
                if existing:
                    continue
                session.add(RawCnPpi(**rec))
                written += 1
        return written
