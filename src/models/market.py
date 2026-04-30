"""Market data models — raw (append-only) and curated (adjusted).

- Raw layer: direct API dump, never modified
- Curated layer: cleaned, forward-adjusted (前复权)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


# ──────────────────────────────────────────
#  RAW LAYER (append-only)
# ──────────────────────────────────────────

class RawStockDaily(TimestampMixin, Base):
    """A-share daily OHLCV — raw API response, immutable."""
    __tablename__ = "raw_stock_daily"
    __table_args__ = (
        {"comment": "A股日线 — 原始API返回，不可变"},
    )

    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_stock_daily_code_date"),
        {"comment": "A股日线 — 原始API返回，不可变"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    pre_close: Mapped[float] = mapped_column(Float, nullable=False)
    change: Mapped[float] = mapped_column(Float, nullable=False)
    pct_chg: Mapped[float] = mapped_column(Float, nullable=False)
    vol: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(手)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(千元)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawCryptoOhlcv(TimestampMixin, Base):
    """Crypto OHLCV — raw API response, immutable."""
    __tablename__ = "raw_crypto_ohlcv"
    __table_args__ = (
        {"comment": "加密币K线 — 原始API返回，不可变"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    timeframe: Mapped[str] = mapped_column(
        String(8), nullable=False, comment="1d | 4h | 1h"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


# ──────────────────────────────────────────
#  CURATED LAYER (SCD2 with forward adjustment)
# ──────────────────────────────────────────

class CuratedStockDailyAdj(TimestampMixin, Base):
    """A-share daily OHLCV — forward-adjusted (前复权)."""
    __tablename__ = "curated_stock_daily_adj"
    __table_args__ = (
        {"comment": "A股日线 — 前复权清洗数据，SCD2版本管理"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open_adj: Mapped[float] = mapped_column(Float, nullable=False)
    high_adj: Mapped[float] = mapped_column(Float, nullable=False)
    low_adj: Mapped[float] = mapped_column(Float, nullable=False)
    close_adj: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(手)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(千元)")
    adj_factor: Mapped[float] = mapped_column(
        Float, nullable=False, comment="当日前复权因子"
    )

    # SCD2 validity (data revisions, e.g. after an ex-dividend)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    version: Mapped[int] = mapped_column(
        default=1, comment="Data revision version"
    )


class CuratedCryptoOhlcv(TimestampMixin, Base):
    """Crypto OHLCV — cleaned data."""
    __tablename__ = "curated_crypto_ohlcv"
    __table_args__ = (
        {"comment": "加密币K线 — 清洗数据"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)


# ──────────────────────────────────────────
#  DAILY BASIC (每日基本面指标)
# ──────────────────────────────────────────

class RawDailyBasic(TimestampMixin, Base):
    """A-share daily basic data — PE, PB, turnover rate, market cap, etc.

    Source: Tushare daily_basic API
    API fields: ts_code, trade_date, close, turnover_rate, turnover_rate_f,
                volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
                total_share, float_share, free_share, total_mv, circ_mv
    """
    __tablename__ = "raw_daily_basic"
    __table_args__ = (
        {"comment": "A股每日基本面指标 — PE/PB/换手率/市值"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    close: Mapped[float] = mapped_column(Float, nullable=False, comment="收盘价")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率(%)")
    turnover_rate_f: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="自由流通股换手率(%)")
    volume_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="量比")
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市盈率(静态)")
    pe_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市盈率(TTM)")
    pb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市净率")
    ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市销率")
    ps_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市销率(TTM)")
    dv_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股息率(%)")
    dv_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股息率(TTM)")
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总市值(万元)")
    circ_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通市值(万元)")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总股本(万股)")
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通股本(万股)")
    free_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="自由流通股本(万股)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStkMins(TimestampMixin, Base):
    """股票分钟行情 (stk_mins).

    Source: Tushare stk_mins API
    1-min / 5-min / 15-min / 30-min / 60-min bars.
    Rate-limited at 2 calls/min — pull selectively.
    """
    __tablename__ = "raw_stk_mins"
    __table_args__ = (
        {"comment": "股票分钟行情 — 5min K线，2次/分钟限流"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_time: Mapped[Optional[str]] = mapped_column(
        String(19), nullable=True, index=True, comment="交易时间 YYYY-MM-DD HH:MM:SS"
    )
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额")

    def __repr__(self):
        return f"<RawStkMins({self.ts_code}, {self.trade_time})>"
