"""现金流量表 VIP — CashFlowVipCollector"""

from __future__ import annotations

import json

from src.db.session import db_session
from src.models.fundamental import RawCashFlow
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CashFlowVipCollector(BaseTushareCollector):
    """现金流量表 VIP 全量 collector."""

    def __init__(self, token: str):
        super().__init__("cashflow_vip", token)

    @property
    def checkpoint_key(self):
        return "period"

    def fetch(self, period: str = "", **kwargs) -> list[dict]:
        params = {}
        if period:
            params["period"] = period
        return self.api_call("cashflow_vip", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {
            "ts_code", "ann_date", "f_ann_date", "end_date",
            "comp_type", "report_type", "end_type", "update_flag",
        }
        validated = []
        for row in raw:
            rec = {}
            for k, v in row.items():
                if k in STR_FIELDS:
                    rec[k] = v
                elif k == "raw_json":
                    continue
                else:
                    rec[k] = _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCashFlow).filter_by(
                    ts_code=rec["ts_code"],
                    end_date=rec["end_date"],
                    report_type=rec.get("report_type"),
                ).first()
                if existing:
                    continue
                session.add(RawCashFlow(**rec))
                written += 1
        return written
