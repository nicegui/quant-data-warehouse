"""Models for 限售解禁 + 外汇黄金 + 消费 + 房地产 — akshare batch 2."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawRestrictedRelease(TimestampMixin, Base):
    """限售股解禁明细 — akshare stock_restricted_release_detail_em()."""

    __tablename__ = "raw_restricted_release"
    __table_args__ = (
        UniqueConstraint("stock_code", "release_date", "release_type", name="uq_rr_code_date_type"),
        {"comment": "限售股解禁明细 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    stock_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="股票简称")
    release_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="解禁日期")
    release_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="限售股类型")
    planned_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="解禁数量(万股)")
    actual_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="实际解禁数量(万股)")
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="实际解禁市值(万元)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawFxGold(TimestampMixin, Base):
    """外汇+黄金储备 — akshare macro_china_fx_gold()."""

    __tablename__ = "raw_fx_gold"
    __table_args__ = (
        UniqueConstraint("month", name="uq_fg_month"),
        {"comment": "外汇黄金储备 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="月份")
    gold_reserve: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="黄金储备(万盎司)")
    gold_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="黄金储备同比(%)")
    gold_mom: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="黄金储备环比(%)")
    fx_reserve: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="外汇储备(亿美元)")
    fx_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="外汇储备同比(%)")
    fx_mom: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="外汇储备环比(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawConsumerGoods(TimestampMixin, Base):
    """社会消费品零售总额 — akshare macro_china_consumer_goods_retail()."""

    __tablename__ = "raw_consumer_goods"
    __table_args__ = (
        UniqueConstraint("month", name="uq_cg_month"),
        {"comment": "社会消费品零售总额 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="月份")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当月值(亿)")
    yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="同比增长(%)")
    mom: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="环比增长(%)")
    cumulative: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="累计值(亿)")
    cum_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="累计同比增长(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawRealEstate(TimestampMixin, Base):
    """国房景气指数 — akshare macro_china_real_estate()."""

    __tablename__ = "raw_real_estate"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_re_date"),
        {"comment": "国房景气指数 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="景气指数值")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    chg_3m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近3月涨跌幅(%)")
    chg_6m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近6月涨跌幅(%)")
    chg_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近1年涨跌幅(%)")
    chg_2y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近2年涨跌幅(%)")
    chg_3y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近3年涨跌幅(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
