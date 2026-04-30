"""基金基本信息 — FundBasicCollector

Tushare fund_basic API — 基金基本信息 (全量拉取, 无 checkpoint).
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.fund import RawFundBasic
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FundBasicCollector(BaseTushareCollector):
    """基金基本信息 collector (全量替换, 无 checkpoint).

    API: pro.fund_basic(market=...)
    Fields: ts_code, name, management, custodian, fund_type, found_date,
            issue_date, issue_amount, invest_type, type, trustee,
            purc_startdate, red_startdate, m_fee, c_fee, benchmark, status
    """

    def __init__(self, token: str):
        super().__init__("fund_basic", token)

    def fetch(self, market: str = "E", **kwargs) -> list[dict]:
        """Fetch all fund basic info. Default market='E' (ETF)."""
        params: dict[str, Any] = {}
        if market:
            params["market"] = market
        params.update(kwargs)
        return self.api_call("fund_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name"),
                "management": row.get("management"),
                "custodian": row.get("custodian"),
                "fund_type": row.get("fund_type"),
                "found_date": row.get("found_date"),
                "issue_date": row.get("issue_date"),
                "issue_amount": _f(row.get("issue_amount")),
                "invest_type": row.get("invest_type"),
                "type": row.get("type"),
                "trustee": row.get("trustee"),
                "purc_startdate": row.get("purc_startdate"),
                "red_startdate": row.get("red_startdate"),
                "m_fee": _f(row.get("m_fee")),
                "c_fee": _f(row.get("c_fee")),
                "benchmark": row.get("benchmark"),
                "status": row.get("status"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Full replace: clear old data, insert new batch."""
        written = 0
        with db_session() as session:
            # Clear old data
            session.query(RawFundBasic).delete()

            for rec in records:
                session.add(RawFundBasic(**rec))
                written += 1
        return written
