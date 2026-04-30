"""Convertible bond market data models — raw layer."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawCbDaily(TimestampMixin, Base):
    """Convertible bond daily OHLCV — raw API response, immutable."""

    __tablename__ = "raw_cb_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_cb_daily_code_date"),
        {"comment": "可转债日线 — 原始API返回，不可变"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    pre_close: Mapped[float] = mapped_column(Float, nullable=False)
    change: Mapped[float] = mapped_column(Float, nullable=False)
    pct_chg: Mapped[float] = mapped_column(Float, nullable=False)
    vol: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(手)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(千元)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RefCbBasic(TimestampMixin, Base):
    """可转债基本信息 (cb_basic)."""
    __tablename__ = "ref_cb_basic"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    bond_full_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    bond_short_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cb_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    cb_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    stk_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    stk_short_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    maturity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    par: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    issue_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    issue_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    remain_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    maturity_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    rate_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    coupon_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    add_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pay_per_year: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    list_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    delist_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    conv_start_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    conv_end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    conv_stop_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    first_conv_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    conv_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rate_clause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class RawCbIssue(TimestampMixin, Base):
    """可转债发行 (cb_issue)."""
    __tablename__ = "raw_cb_issue"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    res_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    plan_issue_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    issue_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    issue_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    issue_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    onl_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    onl_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    onl_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    onl_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    onl_pch_vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    onl_pch_num: Mapped[Optional[float]] = mapped_column(BigInteger, nullable=True)
    onl_pch_excess: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shd_ration_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    shd_ration_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shd_ration_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    shd_ration_record_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    shd_ration_pay_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    shd_ration_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shd_ration_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shd_ration_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    offl_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawCbRate(TimestampMixin, Base):
    """可转债利率 (cb_rate)."""
    __tablename__ = "raw_cb_rate"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
