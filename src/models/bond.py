"""Bond market data models — raw layer for bond daily OHLCV."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawBondDaily(TimestampMixin, Base):
    """Bond daily OHLCV — raw API response, immutable.

    Source: Tushare bond_daily API
    Fields: ts_code, trade_date, open, high, low, close, pre_close,
            change, pct_chg, vol, amount
    Note: May require specific Tushare permissions/version.
    """

    __tablename__ = "raw_bond_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_bond_daily_code_date"),
        {"comment": "债券日线 — 原始API返回，不可变"},
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
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌额")
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量(手)")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额(千元)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawYcCb(TimestampMixin, Base):
    """国债收益率曲线 (yc_cb).

    Source: Tushare yc_cb API
    Fields: trade_date, ts_code, curve_name, curve_type, curve_term, yield
    """
    __tablename__ = "raw_yc_cb"
    __table_args__ = (
        {"comment": "国债收益率曲线(yc_cb) — 原始数据"},
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)
    ts_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)
    curve_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    curve_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    curve_term: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    yield_: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class RawBondBlk(TimestampMixin, Base):
    """债券大宗交易 (bond_blk)."""
    __tablename__ = "raw_bond_blk"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
