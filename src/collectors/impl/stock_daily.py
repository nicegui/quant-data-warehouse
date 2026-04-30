"""A股日线行情 — StockDailyCollector

Fetches daily bars from Tushare, stores raw, then computes
forward-adjusted (前复权) curated layer.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from src.db.session import db_session
from src.models.market import RawStockDaily, CuratedStockDailyAdj
from src.collectors.base import BaseTushareCollector


class StockDailyCollector(BaseTushareCollector):
    """A-share daily OHLCV data collector."""

    def __init__(self, token: str):
        super().__init__("stock_daily", token)

    def fetch(
        self,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Fetch daily data.

        Args:
            trade_date: Specific trading day (latest if None)
            start_date: Start of date range (YYYYMMDD)
            end_date: End of date range (YYYYMMDD)
        """
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.api_call("daily", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Basic field normalization."""
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "pre_close": float(row.get("pre_close", 0)),
                "change": float(row.get("change", 0)),
                "pct_chg": float(row.get("pct_chg", 0)),
                "vol": float(row.get("vol", 0)),
                "amount": float(row.get("amount", 0)),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Append-only insert into raw_stock_daily with dedup."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStockDaily).filter(
                    RawStockDaily.ts_code == rec["ts_code"],
                    RawStockDaily.trade_date == rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStockDaily(**rec))
                written += 1
        return written

    def compute_curated(self, batch_size: int = 500) -> int:
        """Compute forward-adjusted (前复权) daily bars from raw layer."""
        from src.models.reference import RefAdjFactor

        with db_session() as session:
            ts_codes = [
                r[0] for r in session.query(RawStockDaily.ts_code).distinct().all()
            ]

        total_written = 0
        for ts_code in ts_codes:
            with db_session() as session:
                factors = {
                    f.trade_date: f.adj_factor
                    for f in session.query(RefAdjFactor).filter(
                        RefAdjFactor.ts_code == ts_code
                    ).all()
                }

                if not factors:
                    continue

                existing_dates = set(
                    r[0] for r in session.query(CuratedStockDailyAdj.trade_date).all()
                )

                raw_records = session.query(RawStockDaily).filter(
                    RawStockDaily.ts_code == ts_code,
                ).all()

                for raw in raw_records:
                    adj = factors.get(raw.trade_date)
                    if adj is None:
                        continue

                    if raw.trade_date in existing_dates:
                        continue

                    curated = CuratedStockDailyAdj(
                        trade_date=raw.trade_date,
                        open_adj=round(raw.open * adj, 4),
                        high_adj=round(raw.high * adj, 4),
                        low_adj=round(raw.low * adj, 4),
                        close_adj=round(raw.close * adj, 4),
                        volume=raw.vol,
                        amount=raw.amount,
                        adj_factor=adj,
                        valid_from=datetime.now(timezone.utc),
                        valid_to=None,
                        version=1,
                    )
                    session.add(curated)
                    total_written += 1

        return total_written
