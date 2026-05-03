"""Models for 基金评级+基金经理+信用利差 — akshare v5."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawFundRating(TimestampMixin, Base):
    """基金评级 — akshare fund_rating_all()."""

    __tablename__ = "raw_fund_rating"
    __table_args__ = (
        UniqueConstraint("fund_code", name="uq_fr_code"),
        {"comment": "基金评级(多机构) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    fund_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    manager: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rating_5star: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="5星评级家数")
    shanghai_rating: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="上海证券评级")
    zhaoshang_rating: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="招商证券评级")
    jian_rating: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="济安金信评级")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawFundManager(TimestampMixin, Base):
    """基金经理 — akshare fund_manager_em()."""

    __tablename__ = "raw_fund_manager_ak"
    __table_args__ = (
        UniqueConstraint("name", "company", name="uq_fm_name_comp"),
        {"comment": "基金经理信息 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    fund_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="现任基金代码")
    fund_names: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="现任基金名称")
    tenure: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="累计从业时间")
    aum: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="现任基金资产总规模")
    best_return: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="现任基金最佳回报")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawCreditSpread(TimestampMixin, Base):
    """信用利差 — akshare bond_available_index_cbond()."""

    __tablename__ = "raw_credit_spread"
    __table_args__ = (
        UniqueConstraint("index_name", name="uq_cs_name"),
        {"comment": "信用利差(中债) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    index_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
