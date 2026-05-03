"""Models for analyst ranking — akshare stock_analyst_rank_em()."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawAnalystRank(TimestampMixin, Base):
    """分析师年度排名 — akshare stock_analyst_rank_em(year=...)"""

    __tablename__ = "raw_analyst_rank"
    __table_args__ = (
        UniqueConstraint("name", "year_index", name="uq_analyst_rank_name_year"),
        {"comment": "分析师年度排名 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="序号/排名")
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="分析师名称")
    org: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="分析师单位")
    analyst_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True, comment="分析师ID")
    year_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="年度指数")
    ret_annual: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="年度收益率")
    ret_3m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="3个月收益率")
    ret_6m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="6个月收益率")
    ret_12m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="12个月收益率")
    stock_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="成分股个数")
    industry: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="行业")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")


class RawAnalystDetail(TimestampMixin, Base):
    """分析师跟踪成分股明细 — akshare stock_analyst_detail_em(analyst_id=...)"""

    __tablename__ = "raw_analyst_detail"
    __table_args__ = (
        UniqueConstraint("analyst_id", "stock_code", "entry_date", name="uq_ad_aid_code_date"),
        {"comment": "分析师跟踪成分股明细 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    analyst_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="分析师ID")
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    stock_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="股票名称")
    entry_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="调入日期")
    rating_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="最新评级日期")
    rating: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="当前评级名称")
    entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="调入价格")
    latest_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最新价格")
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="阶段涨跌幅")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
