"""概念板块 — ConceptCollector

concept + concept_detail + ths_member from Tushare API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RefConcept, RefConceptDetail
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

    # ── concept_detail ──

    def fetch_concept_detail(self, concept_code: str) -> list[dict]:
        """Fetch constituent stocks for a concept."""
        return self.api_call(
            "concept_detail", id=concept_code,
        )

    def _rename_detail(self, rec: dict) -> dict:
        """Rename API fields to model columns.

        API: code, name, ts_code, ts_name, weight
        Model: concept_code, concept_name, ts_code, name, weight
        """
        return {
            "concept_code": rec.get("code", ""),
            "concept_name": rec.get("name", ""),
            "ts_code": rec.get("ts_code", ""),
            "name": rec.get("ts_name", ""),
            "weight": rec.get("weight"),
        }

    def store_concept_detail(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                row = self._rename_detail(rec)
                existing = session.query(RefConceptDetail).filter_by(
                    concept_code=row["concept_code"],
                    ts_code=row["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RefConceptDetail(**row))
                written += 1
        return written

    # ── ths_member ──

    def fetch_ths_member(self, concept_code: str) -> list[dict]:
        return self.api_call("ths_member", ts_code=concept_code)
