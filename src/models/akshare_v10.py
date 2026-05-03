"""Models for 宏观高频指标 — akshare v10."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawMacroIndicator(TimestampMixin, Base):
    """宏观高频指标 — 房价/景气/税收/保险/手机/菜篮子/农副/能源/建材/费城半导体/义乌电子/BDI等.
    
    统一模型, 多数API遵循 (日期, 最新值, 涨跌幅...) 8列格式.
    去重: (source, date).
    """

    __tablename__ = "raw_macro_indicator"
    __table_args__ = (
        UniqueConstraint("source", "date", "sub_key", name="uq_mi_src_date_key"),
        {"comment": "宏观高频指标(akshare v10)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="数据来源/API名")
    date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    sub_key: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="子维度(如城市/品类), 无则为''")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主值")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅%")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
