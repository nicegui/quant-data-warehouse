"""指数日线 — IndexCollector

index_daily + sw_daily + index_weight from Tushare API.
"""

from __future__ import annotations

from typing import Any

from src.db.session import db_session
from src.models.index import RawIndexDaily, RawSwDaily, RawIndexWeight
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class IndexCollector(BaseTushareCollector):
    """指数日线 collector."""

    def __init__(self, token: str):
        super().__init__("index_daily", token)

    # ── 指数日线 ──

    def fetch_index(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        params = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("index_daily", **params)

    def store_index(self, records: list[dict]) -> int:
        """Bulk-insert index daily with ON CONFLICT dedup."""
        if not records:
            return 0
        from sqlalchemy import text
        with db_session() as session:
            result = session.execute(
                text("""
                    INSERT INTO raw_index_daily
                        (ts_code, trade_date, \"open\", high, low, close,
                         pre_close, change, pct_chg, vol, amount)
                    VALUES
                        (:ts_code, :trade_date, :open, :high, :low, :close,
                         :pre_close, :change, :pct_chg, :vol, :amount)
                    ON CONFLICT (ts_code, trade_date) DO NOTHING
                """),
                records,  # list of dicts → SQLAlchemy executemany
            )
            written = result.rowcount
        return written

    # ── 申万行业指数 ──

    def fetch_sw_daily(self, trade_date: str = "", start_date: str = "",
                       end_date: str = "", **kwargs) -> list[dict]:
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("sw_daily", **params)

    def store_sw_daily(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawSwDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawSwDaily(**rec))
                written += 1
        return written

    # ── 指数成分权重 ──

    def fetch_index_weight(self, index_code: str, trade_date: str) -> list[dict]:
        """Fetch constituent weights for a given index.

        Args:
            index_code: index code (e.g. '000300.SH', '000905.SH')
            trade_date: YYYYMMDD (monthly)
        """
        return self.api_call("index_weight", index_code=index_code, trade_date=trade_date)

    def store_index_weight(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawIndexWeight).filter_by(
                    index_code=rec["index_code"],
                    con_code=rec["con_code"],
                    trade_date=rec.get("trade_date"),
                ).first()
                if existing:
                    continue
                session.add(RawIndexWeight(**rec))
                written += 1
        return written

    # ── 抽象接口桩 ──
    def fetch(self, **kwargs) -> list[dict]:
        return []
    def validate(self, raw: list[dict]) -> list[dict]:
        return []
    def store_raw(self, records: list[dict]) -> int:
        return 0

    # ══════════════════════════════════════════════════════════
    #  run — full backfill: all indices, all dates
    # ══════════════════════════════════════════════════════════

    def run(self) -> dict:
        """Iterate all index codes, fetch full daily history per code."""
        import time, logging
        from src.db.session import get_session
        logger = logging.getLogger(__name__)

        t0 = time.time()
        total_written = 0
        errors = 0

        # Get all index codes
        from sqlalchemy import text
        session = get_session()
        indices = [r[0] for r in session.execute(text("SELECT ts_code FROM ref_index_basic")).fetchall()]
        session.close()

        logger.info(f"Found {len(indices)} index codes")

        for i, ts_code in enumerate(indices):
            try:
                raw = self.fetch_index(
                    ts_code=ts_code,
                    start_date="19900101",
                    end_date="20260502",
                )
                if raw:
                    validated = self._validate_index(raw)
                    written = self.store_index(validated)
                    total_written += written
            except Exception as e:
                logger.error(f"[{ts_code}] ERROR: {e}")
                errors += 1

            if (i + 1) % 500 == 0:
                elapsed = time.time() - t0
                logger.info(
                    f"[{i+1}/{len(indices)}] {total_written:,} rows | "
                    f"{len(indices)/(elapsed)*(i+1)/len(indices):.1f} idx/s"
                )

            time.sleep(0.21)

        elapsed = time.time() - t0
        logger.info(
            f"index_daily DONE: {len(indices)} indices, "
            f"{total_written:,} rows, {errors} errors, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "indices": len(indices),
            "written": total_written,
            "errors": errors,
            "elapsed": elapsed,
        }

    def _validate_index(self, raw: list[dict]) -> list[dict]:
        from src.collectors.impl._utils import _f
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date", ""),
                "close": _f(row.get("close")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "pre_close": _f(row.get("pre_close")),
                "change": _f(row.get("change")),
                "pct_chg": _f(row.get("pct_chg")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
            })
        return validated
