"""重大新闻 — MajorNewsCollector

Tushare major_news API.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.news import RawMajorNews
from src.collectors.base import BaseTushareCollector


class MajorNewsCollector(BaseTushareCollector):
    """重大新闻 collector."""

    def __init__(self, token: str):
        super().__init__("major_news", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, src: str = "", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        ed = end_date or dt.now().strftime("%Y%m%d")
        sd = start_date or ed
        params = {"start_date": sd, "end_date": ed}
        if src:
            params["src"] = src
        return self.api_call("major_news", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "news_id": row.get("news_id", ""),
                "title": row.get("title", ""),
                "content": row.get("content"),
                "source": row.get("src"),
                "pub_time": row.get("pub_time"),
                "impact_level": row.get("impact_level"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMajorNews).filter_by(news_id=rec["news_id"]).first()
                if existing:
                    continue
                session.add(RawMajorNews(**rec))
                written += 1
        return written
