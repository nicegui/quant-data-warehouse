"""同花顺概念板块 — ThsCollector

ths_daily + ths_hot from Tushare API.
两个 API 共用一个 collector，通过 sub_api 参数区分.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.index import RawThsDaily
from src.models.ths import RawThsHot
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class ThsCollector(BaseTushareCollector):
    """同花顺概念板块 collector.

    Supports:
      - 'ths_daily' — 同花顺概念板块日线
      - 'ths_hot'   — 同花顺热榜
    """

    FREQ_CONFIG = {
        "ths_daily": {
            "api": "ths_daily",
            "model": RawThsDaily,
            "label": "ths_daily",
        },
        "ths_hot": {
            "api": "ths_hot",
            "model": RawThsHot,
            "label": "ths_hot",
        },
    }

    def __init__(self, token: str, sub_api: str = "ths_daily"):
        if sub_api not in self.FREQ_CONFIG:
            raise ValueError(f"sub_api must be one of {list(self.FREQ_CONFIG)}, got {sub_api!r}")
        self.sub_api = sub_api
        cfg = self.FREQ_CONFIG[sub_api]
        super().__init__(cfg["label"], token)
        self._api_name = cfg["api"]
        self._model = cfg["model"]

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", trade_date: str = "", start_date: str = "",
              end_date: str = "", market: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if self.sub_api == "ths_daily":
            if ts_code:
                params["ts_code"] = ts_code
            if trade_date:
                params["trade_date"] = trade_date
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
        elif self.sub_api == "ths_hot":
            if market:
                params["market"] = market
            if trade_date:
                params["trade_date"] = trade_date
        return self.api_call(self._api_name, **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            if self.sub_api == "ths_daily":
                rec = {
                    "ts_code": row.get("ts_code", ""),
                    "trade_date": row.get("trade_date"),
                    "open_val": _f(row.get("open")),
                    "high": _f(row.get("high")),
                    "low": _f(row.get("low")),
                    "close": _f(row.get("close")),
                    "pre_close": _f(row.get("pre_close")),
                    "avg_price": _f(row.get("avg_price")),
                    "change": _f(row.get("change")),
                    "pct_change": _f(row.get("pct_change")),
                    "vol": _f(row.get("vol")),
                    "turnover_rate": _f(row.get("turnover_rate")),
                }
            else:  # ths_hot
                ts_code = row.get("ts_code") or row.get("code") or ""
                if not ts_code:
                    continue  # skip US stocks with null code
                rec = {
                    "trade_date": row.get("trade_date"),
                    "data_type": row.get("data_type"),
                    "ts_code": ts_code,
                    "ts_name": row.get("ts_name"),
                    "rank": _f(row.get("rank")),
                    "pct_change": _f(row.get("pct_change")),
                    "current_price": _f(row.get("current_price")),
                    "hot": _f(row.get("hot")),
                    "concept": row.get("concept"),
                    "rank_time": row.get("rank_time"),
                    "rank_reason": row.get("rank_reason"),
                }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                if self.sub_api == "ths_daily":
                    existing = session.query(self._model).filter_by(
                        ts_code=rec["ts_code"],
                        trade_date=rec["trade_date"],
                    ).first()
                else:  # ths_hot
                    existing = session.query(self._model).filter_by(
                        trade_date=rec["trade_date"],
                        ts_code=rec["ts_code"],
                        rank_time=rec.get("rank_time"),
                    ).first()
                if existing:
                    continue
                session.add(self._model(**rec))
                written += 1
        return written

    def run(self, **kwargs) -> dict:
        import logging, time
        from datetime import datetime as dt, timedelta
        logger = logging.getLogger(__name__)

        if self.sub_api == "ths_hot":
            return self._run_hot(logger)
        else:
            return {"status": "skipped", "reason": "ths_daily uses ThsDailyCollector for full run"}

    def _run_hot(self, logger) -> dict:
        """Date-loop: fetch ths_hot for each date."""
        import time as _time
        from datetime import datetime as dt, timedelta
        last_date = self.get_checkpoint_date()
        d = dt(2020, 1, 1) if not last_date else dt.strptime(last_date, "%Y%m%d")
        today = dt.now()
        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0}
        t0 = _time.time()

        while d <= today:
            if d.weekday() >= 5:
                d += timedelta(days=1)
                continue
            date_str = d.strftime("%Y%m%d")
            d += timedelta(days=1)
            if last_date and date_str <= last_date:
                continue
            _time.sleep(0.20)
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
                elapsed = _time.time() - t0
                rate = stats["days"] / elapsed if elapsed > 0 else 0
                logger.info("[%s] %d days, %s rows | %.1f d/s", date_str, stats["days"], f"{stats['written']:,}", rate)

        elapsed = _time.time() - t0
        logger.info("ths_hot DONE: %d days, %s rows, %d errors, %.0fs",
                    stats["days"], f"{stats['written']:,}", stats["errors"], elapsed)
        return {"status": "success", "fetched": stats["fetched"], "written": stats["written"],
                "days": stats["days"], "errors": stats["errors"], "elapsed": elapsed}
