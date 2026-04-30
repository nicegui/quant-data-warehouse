"""审计意见 — FinaAuditCollector

Tushare fina_audit API.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.fundamental import RawFinaAudit
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FinaAuditCollector(BaseTushareCollector):
    """审计意见 collector."""

    def __init__(self, token: str):
        super().__init__("fina_audit", token)

    @property
    def checkpoint_key(self):
        return "end_date"

    def fetch(self, ts_code: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if not (ts_code or end_date):
            ts_code = "000001.SZ"
        if ts_code:
            params["ts_code"] = ts_code
        if end_date:
            params["end_date"] = end_date
        return self.api_call("fina_audit", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "ann_date": row.get("ann_date"),
                "end_date": row.get("end_date"),
                "audit_result": row.get("audit_result", ""),
                "audit_fees": _f(row.get("audit_fees")),
                "audit_agency": row.get("audit_agency", ""),
                "audit_sign": row.get("audit_sign", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinaAudit).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinaAudit(**rec))
                written += 1
        return written
