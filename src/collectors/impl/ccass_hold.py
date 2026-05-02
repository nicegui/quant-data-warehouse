"""中央结算系统持股汇总 — CcassHoldCollector

Tushare ccass_hold API: 香港中央结算系统持股汇总。
数据从 2021 年中开始，覆盖全历史。单次最大 5000 条，需周粒度分块。
"""

import json
from src.db.session import db_session
from src.models.hk_market import RawCcassHold
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class CcassHoldCollector(BaseTushareCollector):
    """中央结算系统持股汇总采集器。"""

    def __init__(self, token: str):
        super().__init__("ccass_hold", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, start_date: str = "", end_date: str = "",
              trade_date: str = "", **kwargs) -> list[dict]:
        """Fetch CCASS holdings for a date range or single date.

        Weekly chunks (~5 trading days) recommended to stay under 5000 limit.
        """
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        elif start_date and end_date:
            params["start_date"] = start_date
            params["end_date"] = end_date
        return self.api_call("ccass_hold", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {"trade_date", "ts_code", "name"}
        validated = []
        for row in raw:
            rec = {}
            for k, v in row.items():
                if k == "raw_json":
                    continue
                rec[k] = v if k in STR_FIELDS else _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Dedup by (ts_code, trade_date)."""
        return self._store_dedup(
            RawCcassHold, records,
            ["ts_code", "trade_date"],
        )
