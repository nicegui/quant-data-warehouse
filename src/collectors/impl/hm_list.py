"""游资名录 — HmListCollector (one-shot)."""

from __future__ import annotations

import json
import logging
from typing import Any

from src.db.session import db_session
from src.models.hm_list import RawHmList
from src.collectors.base import BaseTushareCollector

logger = logging.getLogger(__name__)


class HmListCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("hm_list", token)

    def fetch(self, name: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if name:
            params["name"] = name
        return self.api_call("hm_list", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for x in raw:
            validated.append({
                "name": str(x.get("name", "")),
                "desc": str(x.get("desc", "")) if x.get("desc") else None,
                "orgs": json.dumps(x.get("orgs"), ensure_ascii=False) if x.get("orgs") else None,
                "raw_json": json.dumps(x, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawHmList, records, ["name"])


    def run(self, **kwargs) -> dict:
        raw = self.fetch()
        if not raw:
            return {"status": "empty", "fetched": 0, "written": 0}
        validated = self.validate(raw)
        written = self.store_raw(validated)
        logger.info("hm_list DONE: %d fetched, %d written", len(validated), written)
        return {"status": "success", "fetched": len(validated), "written": written}
