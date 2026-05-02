"""分红送股 (dividend)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawDividend(TimestampMixin, Base):
    """分红送股数据."""

    __tablename__ = "raw_dividend"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "div_proc", name="uq_div_ts_end_proc"),
        {"comment": "分红送股"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="分红年度")
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True, comment="预案公告日")
    div_proc: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实施进度")
    stk_div: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股送转")
    stk_bo_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股送股比例")
    stk_co_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股转增比例")
    cash_div: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股分红税后")
    cash_div_tax: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股分红税前")
    record_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="股权登记日")
    ex_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="除权除息日")
    pay_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="派息日")
    div_listdate: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="红股上市日")
    imp_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实施公告日")
    base_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="基准日")
    base_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="基准股本(万)")

    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<RawDividend({self.ts_code} {self.end_date} {self.div_proc})>"
