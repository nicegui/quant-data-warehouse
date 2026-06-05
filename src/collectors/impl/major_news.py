"""重大新闻 — MajorNewsCollector

Tushare major_news API — premium token required.
API fields: title, pub_time, src, url
"""
from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.news import RawMajorNews
from src.collectors.base import BaseTushareCollector


class MajorNewsCollector(BaseTushareCollector):
    """重大新闻 collector — premium."""

    def __init__(self, token: str):
        super().__init__("major_news", token)

    @property
    def checkpoint_key(self):
        return "pub_time"

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
                "title": row.get("title", ""),
                "pub_time": row.get("pub_time"),
                "source": row.get("src"),
                "url": row.get("url"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawMajorNews, records, ["title", "pub_time"])
