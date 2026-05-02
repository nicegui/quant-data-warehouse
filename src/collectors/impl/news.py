"""新闻快讯 — ConsultationCollector."""

import logging
import time
from datetime import datetime, timedelta

from src.collectors.base import BaseTushareCollector
from src.models.news import RawConsultation

logger = logging.getLogger(__name__)


class ConsultationCollector(BaseTushareCollector):
    """新闻快讯 (news / query('news') API).

    覆盖 2018-11-20 至今，按天拉取，每天最多 1500 条。
    datetime 字段做去重键（秒级精度，同秒重复 = 视为重复）。
    """

    model = RawConsultation
    api_name = "news"
    checkpoint_key = "consultation_date"

    def __init__(self, token: str):
        super().__init__("consultation", token)

    def fetch(self, start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        """拉取一天的新快讯。

        Tushare news API 必须用 pro.query('news') 调用，
        且 start_date/end_date 格式为 '2018-11-20 09:00:00'。
        """
        return self.api_call(
            self.api_name,
            start_date=start_date,
            end_date=end_date,
            limit=1500,
        )

    def validate(self, raw: list[dict]) -> list[dict]:
        _s = lambda v: str(v) if v is not None else None
        validated = []
        for x in raw:
            validated.append({
                "datetime": str(x.get("datetime", "")),
                "title": _s(x.get("title")),
                "content": _s(x.get("content")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawConsultation, records, dedup_keys=["datetime"])

    def run(self) -> dict:
        t0 = time.time()
        total, errors, days = 0, 0, 0
        d = datetime(2018, 11, 20)
        end = datetime.now()
        batch_size = 80  # log progress every 80 days

        while d <= end:
            date_str = d.strftime("%Y-%m-%d")
            start = f"{date_str} 00:00:00"
            end_str = f"{date_str} 23:59:59"
            try:
                raw = self.fetch(start_date=start, end_date=end_str)
                if raw:
                    total += self.store_raw(self.validate(raw))
                days += 1
            except Exception as e:
                logger.error(f"[{date_str}] ERROR: {e}")
                errors += 1

            d += timedelta(days=1)

            if days % batch_size == 0:
                logger.info(
                    f"[{date_str}] {days} days, {total:,} rows "
                    f"| {days / (time.time() - t0):.1f} d/s"
                )
            time.sleep(0.21)

        elapsed = int(time.time() - t0)
        logger.info(
            f"consultation DONE: {days} days, {total:,} rows, "
            f"{errors} err, {elapsed}s"
        )
        return {
            "status": "success",
            "written": total,
            "days": days,
            "errors": errors,
            "elapsed": elapsed,
        }
