"""宏观经济 — MacroCollector

Tushare multi-API: cn_cpi, cn_pmi, cn_gdp, cn_m, shibor.
Each API has its own fetch/store — checkpoint per API via base class.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.macro import (
    RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply, RawShibor,
)
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class MacroCollector(BaseTushareCollector):
    """宏观经济 collector (multi-API)."""

    def __init__(self, token: str):
        super().__init__("macro", token)

    @property
    def checkpoint_key(self):
        return "year"  # macro data is yearly/monthly

    # ── CPI ──

    def fetch_cpi(self, start_m: str = "", end_m: str = "", **kwargs) -> list[dict]:
        return self.api_call("cn_cpi", m=end_m) if end_m else self.api_call("cn_cpi")

    def store_cpi(self, records: list[dict]) -> int:
        return self._store_dedup(RawCnCpi, records, ["month"])

    # ── PMI ──

    def fetch_pmi(self, start_m: str = "", end_m: str = "", **kwargs) -> list[dict]:
        return self.api_call("cn_pmi", m=end_m) if end_m else self.api_call("cn_pmi")

    def store_pmi(self, records: list[dict]) -> int:
        return self._store_dedup(RawCnPmi, records, ["month"])

    # ── GDP ──

    def fetch_gdp(self, **kwargs) -> list[dict]:
        return self.api_call("cn_gdp")

    def store_gdp(self, records: list[dict]) -> int:
        return self._store_dedup(RawCnGdp, records, ["quarter"])

    # ── Money Supply ──

    def fetch_money_supply(self, start_m: str = "", end_m: str = "", **kwargs) -> list[dict]:
        return self.api_call("cn_m", m=end_m) if end_m else self.api_call("cn_m")

    def store_money_supply(self, records: list[dict]) -> int:
        return self._store_dedup(RawCnMoneySupply, records, ["month"])

    # ── Shibor ──

    def fetch_shibor(self, date: str = "", **kwargs) -> list[dict]:
        return self.api_call("shibor", date=date) if date else self.api_call("shibor")

    def store_shibor(self, records: list[dict]) -> int:
        return self._store_dedup(RawShibor, records, ["date"])
