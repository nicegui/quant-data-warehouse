"""资金流向 — MoneyflowCollector

moneyflow + moneyflow_mkt_dc + hsgt_top10 + ggt_top10 + margin_detail.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.moneyflow import (
    RawMoneyflow,
    RawMoneyflowMktDc,
    RawHsgtTop10,
    RawGgtTop10,
    RawMarginDetail,
)
from src.collectors.base import BaseTushareCollector


class MoneyflowCollector(BaseTushareCollector):
    """资金流向 collector (multi-API)."""

    def __init__(self, token: str):
        super().__init__("moneyflow", token)

    def fetch_moneyflow(self, trade_date: str) -> list[dict]:
        return self.api_call("moneyflow", trade_date=trade_date)

    def store_moneyflow(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMoneyflow).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawMoneyflow(**rec))
                written += 1
        return written

    # ── 大盘资金流向 ──

    def fetch_moneyflow_mkt_dc(self, trade_date: str) -> list[dict]:
        return self.api_call("moneyflow_mkt_dc", trade_date=trade_date)

    def store_moneyflow_mkt_dc(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMoneyflowMktDc).filter_by(
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawMoneyflowMktDc(**rec))
                written += 1
        return written

    # ── 沪深股通十大成交 ──

    def fetch_hsgt_top10(self, trade_date: str) -> list[dict]:
        return self.api_call("hsgt_top10", trade_date=trade_date)

    def store_hsgt_top10(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawHsgtTop10).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawHsgtTop10(**rec))
                written += 1
        return written

    # ── 港股通十大成交 ──

    def fetch_ggt_top10(self, trade_date: str) -> list[dict]:
        return self.api_call("ggt_top10", trade_date=trade_date)

    def store_ggt_top10(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawGgtTop10).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawGgtTop10(**rec))
                written += 1
        return written

    # ── 融资融券明细 ──

    def fetch_margin_detail(self, trade_date: str) -> list[dict]:
        return self.api_call("margin_detail", trade_date=trade_date)

    def store_margin_detail(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMarginDetail).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawMarginDetail(**rec))
                written += 1
        return written
