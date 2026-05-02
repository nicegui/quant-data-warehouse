"""审计意见 VIP — FinaAuditVipCollector"""
import json
from src.db.session import db_session
from src.models.fundamental import RawFinaAudit
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

class FinaAuditVipCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("fina_audit_vip", token)
    @property
    def checkpoint_key(self):
        return "period"
    def fetch(self, period: str = "", **kwargs) -> list[dict]:
        return self.api_call("fina_audit_vip", **({"period": period} if period else {}))
    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"ts_code", "ann_date", "end_date", "audit_result", "audit_agency", "audit_sign"}
        validated = []
        for row in raw:
            rec = {}
            for k, v in row.items():
                if k == "raw_json": continue
                rec[k] = v if k in STR_FIELDS else _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated
    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinaAudit).filter_by(
                    ts_code=rec["ts_code"], end_date=rec["end_date"]).first()
                if existing: continue
                session.add(RawFinaAudit(**rec)); written += 1
        return written
