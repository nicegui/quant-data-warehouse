"""US stock market data models — raw layer for US daily OHLCV and basic info."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawUsDaily(TimestampMixin, Base):
    """US stock daily OHLCV — raw API response, immutable.

    Source: Tushare us_daily API
    API fields: ts_code, trade_date, open, high, low, close, pre_close,
                pct_change, vol, amount, vwap
    Note: API uses 'pct_change' (not 'pct_chg') and has 'vwap', no 'change'.
    """

    __tablename__ = "raw_us_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_us_daily_code_date"),
        {"comment": "美股日线 — 原始API返回，不可变"},
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
    pct_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    vol: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(股)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(USD)")
    vwap: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="均价")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawUsBasic(TimestampMixin, Base):
    """US stock basic info — raw API response, immutable.

    Source: Tushare us_basic API
    API fields: ts_code, name, enname, classify, list_date, delist_date
    """

    __tablename__ = "raw_us_basic"
    __table_args__ = (
        UniqueConstraint("ts_code", name="uq_raw_us_basic_code"),
        {"comment": "美股基本信息 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="中文名称")
    enname: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="英文名称")
    classify: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="分类")
    list_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="上市日期")
    delist_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="退市日期")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )
