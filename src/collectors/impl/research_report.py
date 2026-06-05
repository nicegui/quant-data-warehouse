"""券商研究报告 — ResearchReportCollector.

Tushare API: research_report
  - start_date/end_date: 日期范围 (YYYYMMDD)
  - limit: 每页最多 1000 条
  - offset: 分页偏移
  - 字段: trade_date, title, report_type, author, name, ts_code, inst_csname, ind_name, url

Strategy: 按周拉取 + offset 分页, checkpoint 记录最后日期.
"""
import logging
import time
from datetime import datetime, timedelta

from src.collectors.base import BaseTushareCollector
from src.models.research_report import RawResearchReport

logger = logging.getLogger(__name__)

_DEFAULT_START = "20170101"


class ResearchReportCollector(BaseTushareCollector):
    """券商研究报告 (research_report API)."""

    model = RawResearchReport
    api_name = "research_report"
    checkpoint_key = "research_report"

    def __init__(self, token: str):
        super().__init__("research_report", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        """Fetch with start_date/end_date pagination (limit 1000 per page)."""
        start_date = kwargs.get("start_date", trade_date)
        end_date = kwargs.get("end_date", trade_date)
        all_records = []
        offset = 0
        while True:
            page = self.api_call(
                self.api_name,
                start_date=start_date,
                end_date=end_date,
                limit=1000,
                offset=offset,
            )
            if not page:
                break
            all_records.extend(page)
            if len(page) < 1000:
                break
            offset += 1000
            time.sleep(0.25)
        return all_records

    def validate(self, raw: list[dict]) -> list[dict]:
        _s = lambda v: str(v) if v is not None else None
        validated = []
        for x in raw:
            validated.append({
                "trade_date": str(x.get("trade_date", "")),
                "title": str(x.get("title", "")),
                "report_type": _s(x.get("report_type")),
                "author": _s(x.get("author")),
                "name": _s(x.get("name")),
                "ts_code": _s(x.get("ts_code")),
                "inst_csname": _s(x.get("inst_csname")),
                "ind_name": _s(x.get("ind_name")),
                "url": _s(x.get("url")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawResearchReport, records, ["trade_date", "title"])

    def run(self) -> dict:
        t0 = time.time()
        total, errors, windows = 0, 0, 0

        # Checkpoint: last date processed
        last_date = self.get_checkpoint_date()
        if last_date:
            start_dt = datetime.strptime(last_date, "%Y%m%d") + timedelta(days=1)
        else:
            start_dt = datetime(2017, 1, 1)

        end_dt = datetime.now()

        # Pull in 7-day windows
        WINDOW_DAYS = 7
        d = start_dt
        while d <= end_dt:
            chunk_end = min(d + timedelta(days=WINDOW_DAYS - 1), end_dt)
            sd = d.strftime("%Y%m%d")
            ed = chunk_end.strftime("%Y%m%d")
            try:
                raw = self.fetch(start_date=sd, end_date=ed)
                if raw:
                    written = self.store_raw(self.validate(raw))
                    total += written
                    self._update_checkpoint(ed, written)
                windows += 1
            except Exception as e:
                msg = str(e)
                if "频率超限" in msg:
                    logger.warning(f"[{sd}~{ed}] rate-limited, sleep 60s")
                    time.sleep(60)
                    errors += 1
                    continue  # retry same window
                else:
                    logger.error(f"[{sd}~{ed}] ERROR: {e}")
                    errors += 1
            d = chunk_end + timedelta(days=1)

            if windows % 20 == 0 and windows > 0:
                logger.info(f"[{sd}~{ed}] {windows} windows, {total:,} rows | {windows / (time.time() - t0):.1f} w/s")
            time.sleep(0.25)

        elapsed = time.time() - t0
        logger.info(f"research_report DONE: {windows} windows, {total:,} rows, {errors} err, {int(elapsed)}s")
        return {"status": "success", "written": total, "windows": windows, "errors": errors, "elapsed": elapsed}
