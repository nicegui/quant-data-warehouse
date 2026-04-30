"""Options / 期权数据."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin

class RefOptBasic(TimestampMixin, Base):
    """期权基本信息 (opt_basic)."""
    __tablename__ = "ref_opt_basic"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    per_unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    opt_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    opt_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    call_put: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    exercise_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    exercise_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    s_month: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    maturity_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    list_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    list_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    delist_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    last_edate: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    last_ddate: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    quote_unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    min_price_chg: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

class RawOptDaily(TimestampMixin, Base):
    """期权日线 (opt_daily)."""
    __tablename__ = "raw_opt_daily"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    pre_settle: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    settle: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
