"""概念板块 — ConceptCollector

concept + ths_member from Tushare API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RefConcept
from src.collectors.base import BaseTushareCollector


class ConceptCollector(BaseTushareCollector):
    """概念板块 collector."""

    def __init__(self, token: str):
        super().__init__("concept", token)

    def fetch_concepts(self) -> list[dict]:
        """Fetch all concept categories."""
        return self.api_call("concept")

    def store_concepts(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefConcept).filter_by(
                    code=rec["code"]
                ).first()
                if existing:
                    continue
                session.add(RefConcept(**rec))
                written += 1
        return written

    def fetch_ths_member(self, concept_code: str) -> list[dict]:
        return self.api_call("ths_member", ts_code=concept_code)
