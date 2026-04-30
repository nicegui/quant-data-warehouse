"""Interest rates / 利率数据."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin

class RawShiborLpr(TimestampMixin, Base):
    """LPR利率 (shibor_lpr)."""
    __tablename__ = "raw_shibor_lpr"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True, unique=True)
    y1: Mapped[Optional[float]] = mapped_column("1y", Float, nullable=True)
    y5: Mapped[Optional[float]] = mapped_column("5y", Float, nullable=True)

class RawShiborQuote(TimestampMixin, Base):
    """Shibor报价 (shibor_quote)."""
    __tablename__ = "raw_shibor_quote"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    bank: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    on_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    on_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w1_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w1_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w2_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w2_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m1_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m1_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m3_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m3_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m6_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m6_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m9_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m9_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y1_b: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y1_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawLibor(TimestampMixin, Base):
    """Libor利率."""
    __tablename__ = "raw_libor"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    curr_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    on: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m6: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m12: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawHibor(TimestampMixin, Base):
    """Hibor利率."""
    __tablename__ = "raw_hibor"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    on: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    w2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m6: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m12: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawWzIndex(TimestampMixin, Base):
    """温州民间借贷利率."""
    __tablename__ = "raw_wz_index"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    comp_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    center_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    micro_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cm_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sdb_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    om_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aa_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m1_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m3_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m6_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    m12_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    long_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
