"""财务指标 VIP — FinaIndicatorVipCollector"""

import json
from src.db.session import db_session
from src.models.fina_indicator import RawFinaIndicator
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class FinaIndicatorVipCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("fina_indicator_vip", token)

    @property
    def checkpoint_key(self):
        return "period"

    def fetch(self, period: str = "", **kwargs) -> list[dict]:
        return self.api_call("fina_indicator_vip", **({"period": period} if period else {}))

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"ts_code", "ann_date", "end_date", "update_flag"}
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
        return self._store_dedup(RawFinaIndicator, records, ["ts_code", "end_date", "ann_date"])
