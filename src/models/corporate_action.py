"""Corporate action models — 停复牌、分红送股.

- RawSuspendD: 每日停复牌 (suspend_d)
- RawDividend: 分红送股 (dividend)
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawSuspendD(TimestampMixin, Base):
    """每日停复牌信息 (suspend_d).

    Source: Tushare suspend_d API
    One row per stock per day (only stocks that are suspended/have suspension events).
    """
    __tablename__ = "raw_suspend_d"
    __table_args__ = (
        {"comment": "每日停复牌信息 — 仅记录有停复牌事件的股票"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    suspend_timing: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="停牌时段"
    )
    suspend_type: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="S=停牌 R=复牌"
    )

    def __repr__(self):
        return f"<RawSuspendD({self.ts_code}, {self.trade_date}, {self.suspend_type})>"


class RawDividend(TimestampMixin, Base):
    """分红送股数据 (dividend).

    Source: Tushare dividend API
    Covers cash dividends, stock dividends, rights issues, etc.
    """
    __tablename__ = "raw_dividend"
    __table_args__ = (
        {"comment": "分红送股 — 现金分红/送股/转增/配股"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    end_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="分送年度"
    )
    ann_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="公告日期"
    )
    div_proc: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="预案/实施"
    )
    stk_div: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="每股送转"
    )
    stk_bo_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="每股送股比例"
    )
    stk_co_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="每股转增比例"
    )
    cash_div: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="每股派息(税前)"
    )
    cash_div_tax: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="每股派息(税后)"
    )
    record_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="股权登记日"
    )
    ex_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="除权除息日"
    )
    pay_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="派息日"
    )
    div_listdate: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="红股上市日"
    )
    imp_ann_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="实施公告日"
    )

    def __repr__(self):
        return f"<RawDividend({self.ts_code}, {self.ex_date}, div={self.cash_div})>"


class RawSuspend(TimestampMixin, Base):
    """停复牌信息(全量) (suspend)."""
    __tablename__ = "raw_suspend"
    __table_args__ = ({"comment": "停复牌信息(全量) — 历史记录"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    suspend_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    resume_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    suspend_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
