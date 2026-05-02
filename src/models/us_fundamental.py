"""Models for yfinance US fundamental data — dividends, splits, recommendations, institutional holders, company info."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawUsDividend(TimestampMixin, Base):
    """美股分红历史 — yfinance Ticker.dividends"""
    __tablename__ = "raw_us_dividend"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_us_dividend_symbol_date"),
        {"comment": "美股分红历史 — yfinance"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="除息日")
    dividend: Mapped[float] = mapped_column(Float, nullable=False, comment="每股分红")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawUsSplit(TimestampMixin, Base):
    """美股拆股历史 — yfinance Ticker.splits"""
    __tablename__ = "raw_us_split"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_us_split_symbol_date"),
        {"comment": "美股拆股历史 — yfinance"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="拆股日期")
    split_ratio: Mapped[float] = mapped_column(Float, nullable=False, comment="拆股比例")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawUsRecommendation(TimestampMixin, Base):
    """美股分析师评级 — yfinance Ticker.recommendations"""
    __tablename__ = "raw_us_recommendation"
    __table_args__ = (
        UniqueConstraint("symbol", "date", "firm", name="uq_us_recommendation_symbol_date_firm"),
        {"comment": "美股分析师评级 — yfinance"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="评级日期")
    firm: Mapped[str] = mapped_column(String(128), nullable=False, comment="机构名称")
    to_grade: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="调整后评级")
    from_grade: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="调整前评级")
    action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="评级动作")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawUsInstitutional(TimestampMixin, Base):
    """美股机构持仓 — yfinance Ticker.institutional_holders"""
    __tablename__ = "raw_us_institutional"
    __table_args__ = (
        UniqueConstraint("symbol", "date_reported", "holder", name="uq_us_institutional_symbol_date_holder"),
        {"comment": "美股机构持仓 — yfinance"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    date_reported: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="报告日期")
    holder: Mapped[str] = mapped_column(String(256), nullable=False, comment="机构名称")
    pct_held: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持仓占比(%)")
    shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持仓股数")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持仓市值")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawUsInfo(TimestampMixin, Base):
    """美股公司基本信息 — yfinance Ticker.info"""
    __tablename__ = "raw_us_info"
    __table_args__ = (
        UniqueConstraint("symbol", name="uq_us_info_symbol"),
        {"comment": "美股公司基本信息 — yfinance"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    sector: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="行业板块")
    industry: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="细分行业")
    market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总市值")
    employees: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="员工人数")
    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="国家")
    website: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="公司网站")
    long_business_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="业务摘要")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
