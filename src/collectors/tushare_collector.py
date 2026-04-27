"""Tushare Pro collectors — stock daily, consultations, financial reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.session import db_session
from src.models.market import RawStockDaily, CuratedStockDailyAdj
from src.models.news import RawConsultation
from src.models.fundamental import RawFinancialReports, RawFinancialIndicators
from src.models.reference import RefAdjFactor, RefStockBasic, RefTradeCal
from src.models.sentiment import RawTopInst, RawLimitList, RawTopList
from src.collectors.base import BaseTushareCollector


class StockDailyCollector(BaseTushareCollector):
    """A-share daily OHLCV data collector.

    Fetches daily bars from Tushare, stores raw, then computes
    forward-adjusted (前复权) curated layer.
    """

    def __init__(self, token: str):
        super().__init__("stock_daily", token)

    def fetch(self, trade_date: Optional[str] = None, **kwargs) -> list[dict[str, Any]]:
        """Fetch daily data. If trade_date is None, fetches latest trading day."""
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
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
                # Dedup by (ts_code, trade_date)
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
        """Compute forward-adjusted (前复权) daily bars from raw layer.

        Formula: adj_price = raw_price * adj_factor
        where adj_factor = cumprod of split/dividend adjustment.
        """
        from src.models.reference import RefAdjFactor

        # Get all distinct stocks in raw
        with db_session() as session:
            ts_codes = [
                r[0] for r in session.query(RawStockDaily.ts_code).distinct().all()
            ]

        total_written = 0
        for ts_code in ts_codes:
            with db_session() as session:
                # Get adjustment factors for this stock
                factors = {
                    f.trade_date: f.adj_factor
                    for f in session.query(RefAdjFactor).filter(
                        RefAdjFactor.ts_code == ts_code
                    ).all()
                }

                if not factors:
                    continue

                # Get unprocessed raw data
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


class ConsultationCollector(BaseTushareCollector):
    """Tushare news/consultation collector (每5分钟爬一次)."""

    def __init__(self, token: str):
        super().__init__("consultations", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch latest consultations."""
        src = kwargs.get("src", "sina")
        return self.api_call("news", src=src)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "news_id": str(row.get("id", "")),
                "title": row.get("title", ""),
                "content": row.get("content"),
                "source": row.get("source"),
                "pub_time": row.get("datetime"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Upsert by news_id."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawConsultation).filter(
                    RawConsultation.news_id == rec["news_id"]
                ).first()
                if existing:
                    continue
                session.add(RawConsultation(**rec))
                written += 1
        return written


class StockBasicCollector(BaseTushareCollector):
    """Stock master data (全量更新，每周一次)."""

    def __init__(self, token: str):
        super().__init__("stock_basic", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("stock_basic", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
                "area": row.get("area"),
                "industry": row.get("industry"),
                "market": row.get("market"),
                "list_date": row.get("list_date"),
                "delist_date": row.get("delist_date"),
                "is_hs": row.get("is_hs"),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Replace stock basic reference data."""
        written = 0
        with db_session() as session:
            # Clear and repopulate (this is reference data, small table)
            session.query(RefStockBasic).delete()
            for rec in records:
                session.add(RefStockBasic(**rec))
                written += 1
        return written


class FinancialReportCollector(BaseTushareCollector):
    """Financial reports collector."""

    def __init__(self, token: str):
        super().__init__("financial_reports", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("fina_mainbz_vip", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "revenue": self._safe_float(row.get("revenue")),
                "operating_profit": self._safe_float(row.get("operating_profit")),
                "net_profit": self._safe_float(row.get("net_profit")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialReports).filter(
                    RawFinancialReports.ts_code == rec["ts_code"],
                    RawFinancialReports.end_date == rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialReports(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class FinancialIndicatorCollector(BaseTushareCollector):
    """Financial indicators collector (ROE/EPS/PE/PB)."""

    def __init__(self, token: str):
        super().__init__("financial_indicators", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("fina_indicator_vip", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "eps": self._safe_float(row.get("eps")),
                "roe": self._safe_float(row.get("roe")),
                "bps": self._safe_float(row.get("bps")),
                "pe": self._safe_float(row.get("pe")),
                "pb": self._safe_float(row.get("pb")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialIndicators).filter(
                    RawFinancialIndicators.ts_code == rec["ts_code"],
                    RawFinancialIndicators.end_date == rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialIndicators(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class AdjFactorCollector(BaseTushareCollector):
    """Forward adjustment factor collector."""

    def __init__(self, token: str):
        super().__init__("adj_factor", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        params = {}
        start_date = kwargs.get("start_date", "20000101")
        trade_date = kwargs.get("trade_date")
        if trade_date:
            params["trade_date"] = trade_date
        else:
            params["start_date"] = start_date
        return self.api_call("adj_factor", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "adj_factor": float(row.get("adj_factor", 1)),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefAdjFactor).filter(
                    RefAdjFactor.ts_code == rec["ts_code"],
                    RefAdjFactor.trade_date == rec["trade_date"],
                ).first()
                if existing:
                    existing.adj_factor = rec["adj_factor"]
                else:
                    session.add(RefAdjFactor(**rec))
                written += 1
        return written


class TopInstCollector(BaseTushareCollector):
    """龙虎榜机构成交明细 — Tushare top_inst."""

    def __init__(self, token: str):
        super().__init__("top_inst", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict[str, Any]]:
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        else:
            # Default to latest trading day
            from datetime import datetime as dt
            params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("top_inst", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "exalter": row.get("exalter"),
                "buy": self._safe_float(row.get("buy")) or 0,
                "buy_rate": self._safe_float(row.get("buy_rate")),
                "sell": self._safe_float(row.get("sell")) or 0,
                "sell_rate": self._safe_float(row.get("sell_rate")),
                "net_buy": self._safe_float(row.get("net_buy")) or 0,
                "side": row.get("side"),
                "reason": row.get("reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawTopInst).filter(
                    RawTopInst.ts_code == rec["ts_code"],
                    RawTopInst.trade_date == rec["trade_date"],
                    RawTopInst.side == rec["side"],
                ).first()
                if existing:
                    continue
                session.add(RawTopInst(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
