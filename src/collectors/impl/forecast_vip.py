"""业绩预告 VIP — ForecastVipCollector"""

import json
from src.db.session import db_session
from src.models.fundamental import RawForecast
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ForecastVipCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("forecast_vip", token)

    @property
    def checkpoint_key(self):
        return "period"

    def fetch(self, period: str = "", **kwargs) -> list[dict]:
        return self.api_call("forecast_vip", **({"period": period} if period else {}))

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"ts_code", "ann_date", "end_date", "type", "first_ann_date", "summary", "change_reason"}
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
        return self._store_dedup(RawForecast, records, ["ts_code", "end_date"])
