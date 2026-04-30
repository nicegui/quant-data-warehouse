"""FX / 外汇数据."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin

class RawFxDaily(TimestampMixin, Base):
    """外汇日线 (fx_daily)."""
    __tablename__ = "raw_fx_daily"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    bid_open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bid_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bid_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bid_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask_open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tick_qty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RefFxBasic(TimestampMixin, Base):
    """外汇基础信息 (fx_obasic)."""
    __tablename__ = "ref_fx_basic"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    classify: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    min_unit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_unit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pip: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pip_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    traget_spread: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_stop_distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trading_hours: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    break_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
