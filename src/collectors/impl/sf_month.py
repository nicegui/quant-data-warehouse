"""社会融资规模 — SfMonthCollector

Tushare sf_month API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.macro import RawSfMonth
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class SfMonthCollector(BaseTushareCollector):
    """社会融资规模月度数据 collector."""

    def __init__(self, token: str):
        super().__init__("sf_month", token)

    @property
    def checkpoint_key(self):
        return "month"

    def fetch(self, month: str = "", start_period: str = "", end_period: str = "", **kwargs) -> list[dict]:
        """Fetch social financing data.

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
        return self.api_call("sf_month", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "month": row.get("month"),
                "afre": _f(row.get("afre")),
                "t_afre": _f(row.get("t_afre")),
                "t_m_afre": _f(row.get("t_m_afre")),
                "rmb_loan": _f(row.get("rmb_loan")),
                "fx_loan": _f(row.get("fx_loan")),
                "entrust_loan": _f(row.get("entrust_loan")),
                "trust_loan": _f(row.get("trust_loan")),
                "undisc_bill": _f(row.get("undisc_bill")),
                "corp_bond": _f(row.get("corp_bond")),
                "gov_bond": _f(row.get("gov_bond")),
                "abs": _f(row.get("abs")),
                "net_fin": _f(row.get("net_fin")),
                "n_stock": _f(row.get("n_stock")),
                "external_loan": _f(row.get("external_loan")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawSfMonth, records, ["month"])
