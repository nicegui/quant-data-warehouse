"""HK market data models — raw layer for Hong Kong stock daily OHLCV."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawHkDaily(TimestampMixin, Base):
    """HK stock daily OHLCV — raw API response, immutable."""

    __tablename__ = "raw_hk_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_hk_daily_code_date"),
        {"comment": "港股日线 — 原始API返回，不可变"},
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
    vol: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(股)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(HKD)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )
