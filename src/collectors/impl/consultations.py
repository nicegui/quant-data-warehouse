"""快讯 — ConsultationCollector

Tushare news API — premium token required.
API returns datetime, content, title. Do NOT pass start_date.
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.news import RawConsultation
from src.collectors.base import BaseTushareCollector


class ConsultationCollector(BaseTushareCollector):
    """快讯咨询 collector — premium."""

    def __init__(self, token: str):
        super().__init__("consultation", token)

    def fetch(self, **kwargs) -> list[dict]:
        # news API breaks with start_date — omit it
        df = self.pro.query("news")
        return df.to_dict(orient="records") if df is not None and not df.empty else []

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "datetime": row.get("datetime", ""),
                "title": row.get("title"),
                "content": row.get("content"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawConsultation).filter_by(
                    datetime=rec["datetime"],
                ).first()
                if existing:
                    continue
                session.add(RawConsultation(**rec))
                written += 1
        return written
