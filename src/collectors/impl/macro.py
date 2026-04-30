"""宏观经济 — MacroCollector

cpi/pmi/gdp/m2/shibor from Tushare API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.macro import RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply, RawShibor
from src.collectors.base import BaseTushareCollector


class MacroCollector(BaseTushareCollector):
    """宏观经济 collector (multi-API)."""

    def __init__(self, token: str):
        super().__init__("macro", token)

    def fetch_cpi(self) -> list[dict]:
        return self.api_call("cn_cpi")

    def store_cpi(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnCpi).filter_by(
                    month=rec["month"]
                ).first()
                if existing:
                    continue
                session.add(RawCnCpi(**rec))
                written += 1
        return written

    def fetch_pmi(self) -> list[dict]:
        return self.api_call("cn_pmi")

    def store_pmi(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnPmi).filter_by(
                    month=rec["month"]
                ).first()
                if existing:
                    continue
                session.add(RawCnPmi(**rec))
                written += 1
        return written

    def fetch_gdp(self) -> list[dict]:
        return self.api_call("cn_gdp")

    def store_gdp(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnGdp).filter_by(
                    quarter=rec["quarter"]
                ).first()
                if existing:
                    continue
                session.add(RawCnGdp(**rec))
                written += 1
        return written

    def fetch_money_supply(self) -> list[dict]:
        return self.api_call("cn_m")

    def store_money_supply(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnMoneySupply).filter_by(
                    month=rec["month"]
                ).first()
                if existing:
                    continue
                session.add(RawCnMoneySupply(**rec))
                written += 1
        return written

    def fetch_shibor(self) -> list[dict]:
        return self.api_call("shibor")

    def store_shibor(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawShibor).filter_by(
                    date=rec["date"]
                ).first()
                if existing:
                    continue
                session.add(RawShibor(**rec))
                written += 1
        return written
