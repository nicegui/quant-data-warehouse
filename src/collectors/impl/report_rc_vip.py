"""卖方盈利预测 — ReportRcVipCollector

Tushare report_rc API: 获取券商（卖方）每天研报的盈利预测数据。
数据从2010年开始，晚间19~22点更新。

API 限制: 3000条/次，需分页（limit/offset）。
"""

import json
from src.db.session import db_session
from src.models.fundamental import RawReportRc
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ReportRcVipCollector(BaseTushareCollector):
    """卖方盈利预测数据采集器。"""

    PAGE_SIZE = 3000

    def __init__(self, token: str):
        super().__init__("report_rc_vip", token)

    @property
    def checkpoint_key(self):
        return "report_date"

    def fetch(self, report_date: str = "", **kwargs) -> list[dict]:
        """Fetch one report_date with offset pagination.

        Args:
            report_date: 'YYYYMMDD' format. Empty = latest day.
        """
        all_rows: list[dict] = []
        offset = 0
        params = {}
        if report_date:
            params["report_date"] = report_date

        while True:
            params["limit"] = self.PAGE_SIZE
            params["offset"] = offset
            df = self.pro.query("report_rc", **params)
            if df is None or df.empty:
                break
            rows = df.to_dict(orient="records")
            all_rows.extend(rows)
            if len(rows) < self.PAGE_SIZE:
                break
            offset += self.PAGE_SIZE

        return all_rows

    def validate(self, raw: list[dict]) -> list[dict]:
        STR_FIELDS = {
            "ts_code", "name", "report_date", "report_title",
            "report_type", "classify", "org_name", "author_name",
            "quarter", "rating",
        }
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
        """Dedup by (ts_code, report_date, org_name, quarter)."""
        return self._store_dedup(
            RawReportRc, records,
            ["ts_code", "report_date", "org_name", "quarter"],
        )
