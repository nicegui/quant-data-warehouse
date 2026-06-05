"""快讯 — ConsultationCollector

Tushare news API — premium token required.
Parameters: src (required), start_date, end_date (format: '2018-11-20 09:00:00')
Max 1500 rows per call; split by hours for high-volume sources (sina).
Sources with historical: sina, eastmoney.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.news import RawConsultation
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ConsultationCollector(BaseTushareCollector):
    """快讯咨询 collector — 支持按 src + 时间段逐批拉取."""

    VALID_SOURCES = [
        "sina", "wallstreetcn", "10jqka", "eastmoney",
        "yuncaijing", "fenghuang", "jinrongjie", "cls", "yicai",
    ]

    def __init__(self, token: str):
        super().__init__("consultation", token)

    @property
    def checkpoint_key(self):
        return "datetime"

    def fetch(self, src: str = "sina", start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        """Fetch news for a source and date range.

        Args:
            src: News source (required) — one of VALID_SOURCES
            start_date: Start datetime string 'YYYY-MM-DD HH:MM:SS'
            end_date: End datetime string 'YYYY-MM-DD HH:MM:SS'
        """
        params: dict[str, Any] = {"src": src}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("news", **params)

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
        return self._store_dedup(RawConsultation, records, ["datetime"])
