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
    year_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="年度指数")
    ret_annual: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="年度收益率")
    ret_3m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="3个月收益率")
    ret_6m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="6个月收益率")
    ret_12m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="12个月收益率")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
