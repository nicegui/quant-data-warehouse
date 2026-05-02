"""同花顺板块日线 — ThsDailyCollector

Tushare ths_daily API — 同花顺板块指数行情。
遍历所有 THS 指数，每个用 start_date/end_date 一次性拉全量。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

from src.db.session import db_session
from src.models.index import RawThsDaily
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class ThsDailyCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("ths_daily", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, ts_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("ths_daily", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for x in raw:
            rec = {
                "raw_json": json.dumps(x, ensure_ascii=False, default=str),
                "ts_code": str(x.get("ts_code", "")),
                "trade_date": str(x.get("trade_date", "")),
                "open_val": _f(x.get("open")),
                "high": _f(x.get("high")),
                "low": _f(x.get("low")),
                "close": _f(x.get("close")),
                "pre_close": _f(x.get("pre_close")),
                "avg_price": _f(x.get("avg_price")),
                "change": _f(x.get("change")),
                "pct_change": _f(x.get("pct_change")),
                "vol": _f(x.get("vol")),
                "turnover_rate": _f(x.get("turnover_rate")),
                "total_mv": _f(x.get("total_mv")),
                "float_mv": _f(x.get("float_mv")),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawThsDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawThsDaily(**rec))
                written += 1
        return written

    def _get_index_codes(self) -> list[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT ts_code FROM ref_ths_index ORDER BY ts_code")
            ).fetchall()
            session.close()
            return [r[0] for r in rows]
        except Exception:
            return []

    def run(self, **kwargs) -> dict:
        codes = self._get_index_codes()
        if not codes:
            logger.warning("No THS index codes found — run ths_index first")
            return {"status": "error", "fetched": 0, "written": 0}

        stats = {"fetched": 0, "written": 0, "errors": 0, "codes": len(codes)}
        t0 = time.time()

        for i, code in enumerate(codes):
            time.sleep(0.20)
            try:
                raw = self.fetch(ts_code=code, start_date="20100101",
                                 end_date=datetime.now().strftime("%Y%m%d"))
            except Exception:
                stats["errors"] += 1
                continue

            if not raw:
                continue

            validated = self.validate(raw)
            written = self.store_raw(validated)
            stats["fetched"] += len(validated)
            stats["written"] += written

            if (i + 1) % 200 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(codes) - i - 1) / rate if rate > 0 else 0
                logger.info("[%s] %d/%d codes, %s rows | %.1f c/s ETA %.0fs",
                            code, i + 1, len(codes),
                            f"{stats['written']:,}", rate, eta)

        elapsed = time.time() - t0
        logger.info("ths_daily DONE: %d codes, %s rows, %d errors, %.0fs",
                    len(codes), f"{stats['written']:,}",
                    stats["errors"], elapsed)
        return {
            "status": "success" if stats["errors"] < len(codes) * 0.1 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "codes": len(codes),
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
