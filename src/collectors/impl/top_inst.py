"""龙虎榜机构成交 — TopInstCollector

Tushare top_inst API.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.sentiment import RawTopInst
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class TopInstCollector(BaseTushareCollector):
    """龙虎榜机构成交明细 collector."""

    def __init__(self, token: str):
        super().__init__("top_inst", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
        return self.api_call("top_inst", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "exalter": row.get("exalter"),
                "buy": _f(row.get("buy"), 0),
                "buy_rate": _f(row.get("buy_rate")),
                "sell": _f(row.get("sell"), 0),
                "sell_rate": _f(row.get("sell_rate")),
                "net_buy": _f(row.get("net_buy"), 0),
                "side": row.get("side"),
                "reason": row.get("reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawTopInst).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                    exalter=rec["exalter"],
                ).first()
                if existing:
                    continue
                session.add(RawTopInst(**rec))
                written += 1
        return written

    # ── Date-loop Run ──────────────────────────────

    def _get_existing_dates(self) -> set[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT DISTINCT trade_date FROM raw_top_inst")
            ).fetchall()
            session.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def run(self, **kwargs) -> dict:
        import logging, time
        from datetime import datetime, timedelta
        logger = logging.getLogger(__name__)

        existing = self._get_existing_dates()

        d = datetime(2015, 1, 1)
        today = datetime.now()
        dp = []
        while d <= today:
            if d.weekday() < 5:
                dp.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)

        last_date = self.get_checkpoint_date()

        stats = {"fetched": 0, "written": 0, "errors": 0, "days": 0, "skipped": 0}
        t0 = time.time()

        for i, d in enumerate(dp):
            if last_date and d <= last_date:
                stats["skipped"] += 1
                continue
            if d in existing:
                continue

            time.sleep(0.20)
            try:
                raw = self.fetch(trade_date=d)
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
            self._update_checkpoint(d, written)

        elapsed = time.time() - t0
        logger.info("top_inst DONE: %d days, %s rows, %d skipped, %.0fs",
                    stats["days"], f"{stats['written']:,}",
                    stats["skipped"], elapsed)
        return {
            "status": "success" if stats["errors"] == 0 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "days": stats["days"],
            "skipped": stats["skipped"],
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
