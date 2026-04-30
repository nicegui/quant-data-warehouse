"""Reference data — stock basic, trade calendar, adj factors."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RefStockBasic(TimestampMixin, Base):
    """Stock master data."""
    __tablename__ = "ref_stock_basic"
    __table_args__ = (
        {"comment": "股票基本信息"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    area: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(4), nullable=True, comment="主板/创业板/科创板")
    list_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delist_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_hs: Mapped[Optional[str]] = mapped_column(String(4), nullable=True, comment="沪深港通标")


class RefTradeCal(TimestampMixin, Base):
    """Trade calendar."""
    __tablename__ = "ref_trade_cal"
    __table_args__ = (
        {"comment": "交易日历"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    cal_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pretrade_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RawNewShare(TimestampMixin, Base):
    """新股上市 (new_share).

    Source: Tushare new_share API
    Fields: ts_code, sub_code, name, ipo_date, issue_date, amount,
            market_amount, price, pe, limit_amount, funds, ballot
    """
    __tablename__ = "raw_new_share"
    __table_args__ = (
        UniqueConstraint("ts_code", "sub_code", name="uq_raw_new_share_code_sub"),
        {"comment": "新股上市 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    sub_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="申购代码")
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="名称")
    ipo_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="上市日期")
    issue_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="发行日期")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="发行数量(万股)")
    market_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="上网发行数量(万股)")
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="发行价格")
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="发行市盈率")
    limit_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="个人申购上限(万股)")
    funds: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="募集资金(亿元)")
    ballot: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="中签率(%?)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RefAdjFactor(TimestampMixin, Base):
    """Forward adjustment factors (前复权因子)."""
    __tablename__ = "ref_adj_factor"
    __table_args__ = (
        {"comment": "前复权因子"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    adj_factor: Mapped[float] = mapped_column(Float, nullable=False)


class RawNameChange(TimestampMixin, Base):
    """股票更名记录 (namechange).

    Source: Tushare namechange API
    Fields: ts_code, name, start_date, end_date, ann_date, change_reason
    """
    __tablename__ = "raw_namechange"
    __table_args__ = (
        {"comment": "股票更名记录 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="股票名称")
    start_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="开始日期")
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="结束日期")
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="变更原因")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RefDisclosureDate(TimestampMixin, Base):
    """财报披露计划 (disclosure_date)."""
    __tablename__ = "ref_disclosure_date"
    __table_args__ = ({"comment": "财报披露计划日期"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    pre_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    actual_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class RawRepoDaily(TimestampMixin, Base):
    """质押式回购日行情 (repo_daily)."""
    __tablename__ = "raw_repo_daily"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    repo_maturity: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_r: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    num: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RawBakBasic(TimestampMixin, Base):
    """备用列表 (bak_basic).

    Source: Tushare bak_basic API
    Fields: trade_date, ts_code, name, industry, area, pe, float_share,
            total_share, total_assets, liquid_assets, fixed_assets, reserved,
            reserved_pershare, eps, bvps, pb, list_date, undp, per_undp,
            rev_yoy, profit_yoy, gpr, npr, holder_num
    """
    __tablename__ = "raw_bak_basic"
    __table_args__ = (
        UniqueConstraint("trade_date", "ts_code", name="uq_raw_bak_basic_date_code"),
        {"comment": "备用列表 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股票名称")
    industry: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="行业")
    area: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="地区")
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市盈率")
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通股本(万股)")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总股本(万股)")
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总资产(亿元)")
    liquid_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动资产(亿元)")
    fixed_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产(亿元)")
    reserved: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="公积金(元)")
    reserved_pershare: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股公积金")
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股收益")
    bvps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股净资产")
    pb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市净率")
    list_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="上市日期")
    undp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="未分配利润(元)")
    per_undp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股未分配利润")
    rev_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收入同比(%)")
    profit_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="利润同比(%)")
    gpr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="毛利率(%)")
    npr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利率(%)")
    holder_num: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="股东人数")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawBakBasic({self.trade_date}, {self.ts_code})>"
