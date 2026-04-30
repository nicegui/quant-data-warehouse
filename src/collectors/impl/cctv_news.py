"""新闻联播 — CctvNewsCollector

Tushare cctv_news API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.news import RawCctvNews
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CctvNewsCollector(BaseTushareCollector):
    """新闻联播 collector."""

    def __init__(self, token: str):
        super().__init__("cctv_news", token)

    @property
    def checkpoint_key(self):
        return "date"

    def fetch(self, date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if date:
            params["date"] = date
        return self.api_call("cctv_news", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "date": row.get("date", ""),
                "title": row.get("title", ""),
                "content": row.get("content"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCctvNews).filter_by(
                    date=rec["date"],
                    title=rec["title"],
                ).first()
                if existing:
                    continue
                session.add(RawCctvNews(**rec))
                written += 1
        return written
