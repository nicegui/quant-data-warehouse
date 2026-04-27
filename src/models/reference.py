"""Reference data — stock basic, trade calendar, adj factors."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RefStockBasic(TimestampMixin, Base):
    """Stock master data."""
    __tablename__ = "ref_stock_basic"
    __table_args__ = (
        {"comment": "股票基本信息"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    area: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(4), nullable=True, comment="主板/创业板/科创板")
    list_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delist_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_hs: Mapped[Optional[str]] = mapped_column(String(4), nullable=True, comment="沪深港通标")


class RefTradeCal(TimestampMixin, Base):
    """Trade calendar."""
    __tablename__ = "ref_trade_cal"
    __table_args__ = (
        {"comment": "交易日历"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    cal_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pretrade_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RefAdjFactor(TimestampMixin, Base):
    """Forward adjustment factors (前复权因子)."""
    __tablename__ = "ref_adj_factor"
    __table_args__ = (
        {"comment": "前复权因子"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    adj_factor: Mapped[float] = mapped_column(Float, nullable=False)
