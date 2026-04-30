"""Models for baostock data sources — stock basic reference."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RefBaostockBasic(TimestampMixin, Base):
    """股票基本信息 — baostock query_stock_basic()"""
    __tablename__ = "ref_baostock_basic"
    __table_args__ = (
        UniqueConstraint("code", name="uq_baostock_basic_code"),
        {"comment": "股票基本信息 — baostock"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    code_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股票名称")
    ipo_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="上市日期")
    out_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="退市日期")
    type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="证券类型(1=股票)")
    status: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="上市状态(1=上市)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
