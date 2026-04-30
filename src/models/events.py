"""Events & calendar / 事件日历."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin

class RawEcoCal(TimestampMixin, Base):
    """财经日历 (eco_cal)."""
    __tablename__ = "raw_eco_cal"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    event: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pre_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    fore_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

class RefBrokerRecommend(TimestampMixin, Base):
    """券商月度荐股 (broker_recommend)."""
    __tablename__ = "ref_broker_recommend"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    broker: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ts_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
