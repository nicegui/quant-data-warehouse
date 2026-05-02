"""券商研究报告 — ResearchReportCollector."""
import logging
import time
from datetime import datetime, timedelta

from src.collectors.base import BaseTushareCollector
from src.models.research_report import RawResearchReport

logger = logging.getLogger(__name__)


class ResearchReportCollector(BaseTushareCollector):
    """券商研究报告 (research_report API)."""

    model = RawResearchReport
    api_name = "research_report"
    checkpoint_key = "research_report"

    def __init__(self, token: str):
        super().__init__("research_report", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        return self.api_call(self.api_name, trade_date=trade_date, limit=1000)

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
        from src.db.session import db_session
        w = 0
        with db_session() as s:
            for r in records:
                e = s.query(RawResearchReport).filter_by(
                    trade_date=r["trade_date"], title=r["title"]
                ).first()
                if not e:
                    s.add(RawResearchReport(**r))
                    w += 1
        return w

    def run(self) -> dict:
        t0 = time.time()
        total, errors, days = 0, 0, 0
        d = datetime(2017, 1, 1)
        end = datetime(2026, 5, 3)

        while d <= end:
            date_str = d.strftime("%Y%m%d")
            try:
                raw = self.fetch(trade_date=date_str)
                if raw:
                    total += self.store_raw(self.validate(raw))
                days += 1
            except Exception as e:
                logger.error(f"[{date_str}] ERROR: {e}")
                errors += 1
            d += timedelta(days=1)

            if days % 200 == 0:
                logger.info(f"[{date_str}] {days} days, {total:,} rows | {days/(time.time()-t0):.1f} d/s")
            time.sleep(0.21)

        logger.info(f"research_report DONE: {days} days, {total:,} rows, {errors} err, {int(time.time()-t0)}s")
        return {"status": "success", "written": total, "days": days, "errors": errors, "elapsed": time.time() - t0}
