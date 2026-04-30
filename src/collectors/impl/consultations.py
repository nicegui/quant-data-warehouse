"""咨询/快讯 — ConsultationCollector

Tushare news/consultation collector (每5分钟爬一次).
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.news import RawConsultation
from src.collectors.base import BaseTushareCollector


class ConsultationCollector(BaseTushareCollector):
    """Tushare news/consultation collector."""

    def __init__(self, token: str):
        super().__init__("consultations", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch latest consultations."""
        src = kwargs.get("src", "sina")
        return self.api_call("news", src=src)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "news_id": str(row.get("id", "")),
                "title": row.get("title", ""),
                "content": row.get("content"),
                "source": row.get("source"),
                "pub_time": row.get("datetime"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Upsert by news_id."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawConsultation).filter(
                    RawConsultation.news_id == rec["news_id"]
                ).first()
                if existing:
                    continue
                session.add(RawConsultation(**rec))
                written += 1
        return written
