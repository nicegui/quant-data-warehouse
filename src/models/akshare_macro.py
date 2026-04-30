"""Models for akshare data sources — CPI / PMI / GDP / MoneySupply / HsgtHist."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawAkshareCpi(TimestampMixin, Base):
    """CPI数据 — akshare macro_china_cpi_yearly()"""
    __tablename__ = "raw_akshare_cpi"
    __table_args__ = (
        UniqueConstraint("date_str", "item", name="uq_akshare_cpi_date_item"),
        {"comment": "CPI数据 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="日期")
    item: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="统计项")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="今值")
    forecast: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预测值")
    previous: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="前值")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawAksharePmi(TimestampMixin, Base):
    """PMI数据 — akshare macro_china_pmi()"""
    __tablename__ = "raw_akshare_pmi"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_akshare_pmi_date"),
        {"comment": "PMI数据 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="月份")
    mfg_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="制造业-指数")
    mfg_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="制造业-同比增长")
    non_mfg_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="非制造业-指数")
    non_mfg_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="非制造业-同比增长")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawAkshareGdp(TimestampMixin, Base):
    """GDP数据 — akshare macro_china_gdp()"""
    __tablename__ = "raw_akshare_gdp"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_akshare_gdp_date"),
        {"comment": "GDP数据 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="季度")
    gdp_abs: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="国内生产总值-绝对值")
    gdp_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="国内生产总值-同比增长")
    pi_abs: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="第一产业-绝对值")
    pi_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="第一产业-同比增长")
    si_abs: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="第二产业-绝对值")
    si_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="第二产业-同比增长")
    ti_abs: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="第三产业-绝对值")
    ti_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="第三产业-同比增长")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawAkshareMoneySupply(TimestampMixin, Base):
    """货币供应量 — akshare macro_china_money_supply()"""
    __tablename__ = "raw_akshare_money_supply"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_akshare_m2_date"),
        {"comment": "货币供应量 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="月份")
    m2_qty: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币和准货币(M2)-数量(亿元)")
    m2_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币和准货币(M2)-同比增长")
    m2_mom: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币和准货币(M2)-环比增长")
    m1_qty: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币(M1)-数量(亿元)")
    m1_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币(M1)-同比增长")
    m1_mom: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币(M1)-环比增长")
    m0_qty: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通中的现金(M0)-数量(亿元)")
    m0_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通中的现金(M0)-同比增长")
    m0_mom: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通中的现金(M0)-环比增长")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawAkshareHsgtHist(TimestampMixin, Base):
    """沪深港通历史资金流向 — akshare stock_hsgt_hist_em()"""
    __tablename__ = "raw_akshare_hsgt_hist"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_akshare_hsgt_date"),
        {"comment": "沪深港通历史资金流向 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="日期")
    net_buy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当日成交净买额")
    buy_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="买入成交额")
    sell_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="卖出成交额")
    cum_net_buy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="历史累计净买额")
    net_flow: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当日资金流入")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
