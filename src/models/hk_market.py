"""HK market data models — raw layer for Hong Kong stock daily OHLCV."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawHkDaily(TimestampMixin, Base):
    """HK stock daily OHLCV — raw API response, immutable."""

    __tablename__ = "raw_hk_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_hk_daily_code_date"),
        {"comment": "港股日线 — 原始API返回，不可变"},
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
    vol: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(股)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(HKD)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )

class RefHkBasic(TimestampMixin, Base):
    """港股列表 (hk_basic)."""
    __tablename__ = "ref_hk_basic"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    fullname: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    enname: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    cn_spell: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    list_status: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    list_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    delist_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    trade_unit: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    isin: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    curr_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

class RawHkMins(TimestampMixin, Base):
    """港股分钟行情 (hk_mins)."""
    __tablename__ = "raw_hk_mins"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_time: Mapped[str] = mapped_column(String(19), nullable=False, index=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RawCcassHold(TimestampMixin, Base):
    """中央结算系统持股汇总 (ccass_hold)."""
    __tablename__ = "raw_ccass_hold"
    __table_args__ = ({"comment": "中央结算系统持股汇总 — 原始数据"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    shareholding: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股量(股)")
    hold_nums: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="参与者数目")
    hold_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="占A股总数百分比")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawCcassHoldDetail(TimestampMixin, Base):
    """中央结算系统持股明细 (ccass_hold_detail)."""
    __tablename__ = "raw_ccass_hold_detail"
    __table_args__ = ({"comment": "CCASS席位持股明细 — 原始数据"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    col_participant_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    col_participant_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    col_shareholding: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    col_shareholding_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawHkHold(TimestampMixin, Base):
    """沪深港股通持股明细 (hk_hold)."""
    __tablename__ = "raw_hk_hold"
    __table_args__ = ({"comment": "港股通持股明细 — 原始数据"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    vol: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="持股数量(股)")
    ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股占比(%)")
    exchange: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawStkAhComparison(TimestampMixin, Base):
    """AH股比价 (stk_ah_comparison)."""
    __tablename__ = "raw_stk_ah_comparison"
    __table_args__ = (
        UniqueConstraint("hk_code", "ts_code", "trade_date", name="uq_ah_comp_code_date"),
        {"comment": "AH股比价数据"},
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hk_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    hk_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    hk_pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hk_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ah_comparison: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ah_premium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
