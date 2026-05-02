"""KPL List (开盘啦榜单) collector — 涨停/炸板/跌停/自然涨停/竞价."""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from src.collectors.base import BaseTushareCollector
from src.models.kpl_list import RawKplList

logger = logging.getLogger(__name__)

TAGS = ["涨停", "炸板", "跌停", "自然涨停", "竞价"]

class KplListCollector(BaseTushareCollector):
    """Collect KPL (开盘啦) board data — limit-up/down, open-up, bidding, etc."""

    model = RawKplList
    api_name = "kpl_list"
    checkpoint_key = "kpl_list"

    def __init__(self, token: str):
        super().__init__("kpl_list", token)

    def fetch(self, trade_date: str, tag: str) -> Optional[list]:
        """Fetch KPL list for a single trade_date + tag."""
        return self.api_call(self.api_name, trade_date=trade_date, tag=tag, limit=8000)

    def validate(self, raw_data: list) -> list:
        """Validate and transform API response to model-compatible dicts."""
        _s = lambda v: str(v) if v is not None else None
        _f = lambda v: float(v) if v is not None else None
        validated = []
        for row in raw_data:
            validated.append({
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")),
                "trade_date": str(row.get("trade_date", "")),
                "lu_time": _s(row.get("lu_time")),
                "ld_time": _s(row.get("ld_time")),
                "open_time": _s(row.get("open_time")),
                "last_time": _s(row.get("last_time")),
                "lu_desc": _s(row.get("lu_desc")),
                "tag": str(row.get("tag", "")),
                "theme": _s(row.get("theme")),
                "net_change": _f(row.get("net_change")),
                "bid_amount": _f(row.get("bid_amount")),
                "status": _s(row.get("status")),
                "bid_change": _f(row.get("bid_change")),
                "bid_turnover": _f(row.get("bid_turnover")),
                "lu_bid_vol": _f(row.get("lu_bid_vol")),
                "pct_chg": _f(row.get("pct_chg")),
                "bid_pct_chg": _f(row.get("bid_pct_chg")),
                "rt_pct_chg": _f(row.get("rt_pct_chg")),
                "limit_order": _f(row.get("limit_order")),
                "amount": _f(row.get("amount")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "free_float": _f(row.get("free_float")),
                "lu_limit_order": _f(row.get("lu_limit_order")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Not called; upsert is inline in run(). Stub for abstract interface."""
        return len(records)

    def run(self, start_date: str = "20200101", end_date: Optional[str] = None) -> dict:
        """Full historical backfill — iterate dates, all 5 tags per date."""
        import time
        from src.db.session import get_session

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        # Checkpoint
        last_date = self.get_checkpoint_date()
        if last_date:
            last_date = last_date.replace("-", "")
            start = datetime.strptime(last_date, "%Y%m%d") + timedelta(days=1)
            start_date = start.strftime("%Y%m%d")
            logger.info(f"Resuming from checkpoint date: {start_date}")

        d = datetime.strptime(start_date, "%Y%m%d")
        end_d = datetime.strptime(end_date, "%Y%m%d")

        total_fetched = 0
        total_written = 0
        errors = 0
        days_processed = 0
        t0 = time.time()

        session = get_session()

        while d <= end_d:
            d_str = d.strftime("%Y%m%d")
            day_written = 0

            for tag in TAGS:
                try:
                    raw = self.fetch(d_str, tag)
                    if raw:
                        validated = self.validate(raw)
                        # upsert by (ts_code, trade_date, tag)
                        for rec in validated:
                            existing = session.query(RawKplList).filter_by(
                                ts_code=rec["ts_code"],
                                trade_date=rec["trade_date"],
                                tag=rec["tag"],
                            ).first()
                            if existing:
                                for k, v in rec.items():
                                    if k != "id":
                                        setattr(existing, k, v)
                            else:
                                session.add(RawKplList(**rec))
                            total_written += 1
                            day_written += 1
                        session.commit()
                        total_fetched += len(raw)
                    time.sleep(0.21)  # rate limit ~5 calls/s
                except Exception as e:
                    logger.error(f"[{d_str}][{tag}] ERROR: {e}")
                    errors += 1
                    session.rollback()

            days_processed += 1
            d += timedelta(days=1)

            # Log every 50 days
            if days_processed % 50 == 0:
                elapsed = time.time() - t0
                d_per_s = days_processed / elapsed if elapsed > 0 else 0
                remaining = None
                days_left = (end_d - d).days + 1
                if d_per_s > 0:
                    remaining = days_left / d_per_s
                logger.info(
                    f"[{d_str}] {days_processed} days, "
                    f"{total_written:,} rows | "
                    f"{d_per_s:.2f} d/s "
                    f"{'ETA ' + str(int(remaining)) + 's' if remaining else ''}"
                )

            # Save checkpoint every 100 days
            if days_processed % 100 == 0:
                self._update_checkpoint(d_str, total_written)

            time.sleep(0.20)

        session.close()

        # Final checkpoint
        self._update_checkpoint(end_date, total_written)
        elapsed = time.time() - t0
        logger.info(
            f"kpl_list DONE: {days_processed} days, "
            f"{total_written:,} rows, {errors} errors, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "fetched": total_fetched,
            "written": total_written,
            "days": days_processed,
            "errors": errors,
            "elapsed": elapsed,
        }
