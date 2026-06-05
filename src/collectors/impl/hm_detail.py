"""游资每日明细 — HmDetailCollector (date-loop)."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime as dt, timedelta
from typing import Any

from src.db.session import db_session
from src.models.hm_detail import RawHmDetail
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class HmDetailCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("hm_detail", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              hm_name: str = "", start_date: str = "", end_date: str = "",
              **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if trade_date: params["trade_date"] = trade_date
        if ts_code: params["ts_code"] = ts_code
        if hm_name: params["hm_name"] = hm_name
        if start_date: params["start_date"] = start_date
        if end_date: params["end_date"] = end_date
        return self.api_call("hm_detail", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for x in raw:
            validated.append({
                "trade_date": str(x.get("trade_date", "")),
                "ts_code": str(x.get("ts_code", "")),
                "ts_name": str(x.get("ts_name", "")) if x.get("ts_name") else None,
                "buy_amount": _f(x.get("buy_amount")),
                "sell_amount": _f(x.get("sell_amount")),
                "net_amount": _f(x.get("net_amount")),
                "hm_name": str(x.get("hm_name", "")) if x.get("hm_name") else None,
                "hm_orgs": str(x.get("hm_orgs", "")) if x.get("hm_orgs") else None,
                "tag": str(x.get("tag", "")) if x.get("tag") else None,
                "raw_json": json.dumps(x, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawHmDetail, records, ["trade_date", "ts_code", "hm_name"])

    def run(self, **kwargs) -> dict:
        last_date = self.get_checkpoint_date()
        d = dt(2022, 8, 1) if not last_date else dt.strptime(last_date, "%Y%m%d")
        today = dt.now()
        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0}
        t0 = time.time()

        while d <= today:
            if d.weekday() >= 5:
                d += timedelta(days=1)
                continue
            date_str = d.strftime("%Y%m%d")
            d += timedelta(days=1)
            if last_date and date_str <= last_date:
                continue
            time.sleep(0.20)
            try:
                raw = self.fetch(trade_date=date_str)
            except Exception:
                stats["errors"] += 1
                continue
            if not raw:
                continue
            validated = self.validate(raw)
            written = self.store_raw(validated)
            stats["fetched"] += len(validated)
            stats["written"] += written
            stats["days"] += 1
            self._update_checkpoint(date_str, written)
            if stats["days"] % 100 == 0:
                elapsed = time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                logger.info("[%s] %d days, %s rows | %.1f d/s", date_str, stats["days"], f"{stats['written']:,}", rate)

        elapsed = time.time() - t0
        logger.info("hm_detail DONE: %d days, %s rows, %d errors, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["errors"], elapsed)
        return {"status": "success", "fetched": stats["fetched"], "written": stats["written"],
                "days": stats["days"], "errors": stats["errors"], "elapsed": elapsed}
