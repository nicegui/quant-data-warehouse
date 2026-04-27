"""Crypto collector (Phase 2 — structure reserved)."""

from __future__ import annotations

from src.collectors.base import BaseCollector


class CryptoOhlcvCollector(BaseCollector):
    """OKX crypto OHLCV collector (reserved for Phase 2)."""

    def __init__(self):
        super().__init__("crypto_ohlcv")

    def fetch(self, **kwargs) -> list[dict]:
        """Not implemented yet — Phase 2."""
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    def store_raw(self, records: list[dict]) -> int:
        return 0
