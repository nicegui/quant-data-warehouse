"""Models for 社融 + 基金仓位 + 公募持仓."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawSocialFinance(TimestampMixin, Base):
    """社融数据 — akshare macro_china_new_financial_credit()."""

    __tablename__ = "raw_social_finance"
    __table_args__ = (
        UniqueConstraint("month", name="uq_sf_month"),
        {"comment": "社融/新增信贷 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="月份")
    social_finance: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="社会融资规模(亿)")
    new_loan: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="新增人民币贷款(亿)")
    m2_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="M2同比(%)")
    m1_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="M1同比(%)")
    m0_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="M0同比(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawFundPosition(TimestampMixin, Base):
    """基金仓位估算 — akshare fund_balance_position_lg()."""

    __tablename__ = "raw_fund_position"
    __table_args__ = (
        UniqueConstraint("trade_date", name="uq_fp_date"),
        {"comment": "基金仓位估算(乐股) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    stock_fund_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股票型基金仓位(%)")
    hybrid_fund_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="混合型基金仓位(%)")
    total_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总仓位(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawFundHolding(TimestampMixin, Base):
    """公募基金持仓明细 — akshare fund_portfolio_hold_em()."""

    __tablename__ = "raw_fund_holding"
    __table_args__ = (
        UniqueConstraint("fund_code", "stock_code", "report_date", name="uq_fh_fund_stock_date"),
        {"comment": "公募基金持仓明细 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="基金代码")
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    stock_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="股票名称")
    report_date: Mapped[str] = mapped_column(String(16), nullable=False, comment="报告期")
    hold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股市值")
    hold_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="占净值比例(%)")
    shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股数")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
