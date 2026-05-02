"""国际期货历史行情 — RawForeignFutures

AKShare futures_foreign_hist data (Brent/WTI etc.)
Dedup: (symbol, date)
"""
from __future__ import annotations

from src.models.base import Base, TimestampMixin
from sqlalchemy import BigInteger, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional


class RawForeignFutures(TimestampMixin, Base):
    """国际期货日线 (futures_foreign_hist).

    Symbol codes: CL=WTI, OIL=Brent, NG=天然气, GC=黄金, SI=白银, etc.
    """
    __tablename__ = "raw_foreign_futures"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_foreign_futures_symbol_date"),
        {"comment": "国际期货日线 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="品种代码(CL/OIL/NG/GC...)")
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True, comment="交易日期(YYYY-MM-DD)")
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="成交量")
    position: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="持仓量")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )
