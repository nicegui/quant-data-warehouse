"""Models for QVIX 恐慌指数 — akshare index_option_*_qvix()."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawQvix(TimestampMixin, Base):
    """期权隐含波动率指数 (中国版VIX)."""

    __tablename__ = "raw_qvix"
    __table_args__ = (
        UniqueConstraint("trade_date", "underlying", name="uq_qvix_date_und"),
        {"comment": "QVIX恐慌指数 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    underlying: Mapped[str] = mapped_column(String(16), nullable=False, comment="标的 (50ETF/300ETF)")
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="QVIX收盘值")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawEpuIndex(TimestampMixin, Base):
    """经济政策不确定性指数 (Baker EPU Index)."""

    __tablename__ = "raw_epu_index"
    __table_args__ = (
        UniqueConstraint("month", "country", name="uq_epu_month_country"),
        {"comment": "EPU经济不确定性指数 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="月份")
    country: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="国家/地区 (China/Global/US)")
    epu_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="EPU指数值")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
