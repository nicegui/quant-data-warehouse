"""Market sentiment models — limit-up/down, dragon-tiger board, margin.

Raw layer only (append-only). No curated layer needed — these are event data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawTopInst(TimestampMixin, Base):
    """龙虎榜机构成交明细 — Tushare top_inst.

    Fields match the Tushare Pro API response.
    Each row = one institution's buy/sell record for one stock on one day.
    """
    __tablename__ = "raw_top_inst"
    __table_args__ = {"comment": "龙虎榜机构成交明细 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    exalter: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="营业部名称/机构席位"
    )
    buy: Mapped[float] = mapped_column(
        Float, nullable=False, default=0, comment="买入金额(元)"
    )
    buy_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="买入占总成交比例(%)"
    )
    sell: Mapped[float] = mapped_column(
        Float, nullable=False, default=0, comment="卖出金额(元)"
    )
    sell_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="卖出占总成交比例(%)"
    )
    net_buy: Mapped[float] = mapped_column(
        Float, nullable=False, default=0, comment="净买入金额(元)"
    )
    side: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="0=买入 1=卖出"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="上榜原因"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawLimitList(TimestampMixin, Base):
    """涨停板股票列表 — Tushare limit_list_d."""
    __tablename__ = "raw_limit_list"
    __table_args__ = {"comment": "涨停板股票列表 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="股票名称"
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="所属行业"
    )
    limit_type: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="涨停类型 (L=涨停, D=跌停)"
    )
    open_vol: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="开盘涨停封单量(万股)"
    )
    close_vol: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="收盘涨停封单量(万股)"
    )
    open_amt: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="开盘涨停封单金额(万元)"
    )
    close_amt: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="收盘涨停封单金额(万元)"
    )
    first_time: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="首次涨停时间"
    )
    last_time: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="最后涨停时间"
    )
    limit_times: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="连续涨停天数"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawTopList(TimestampMixin, Base):
    """龙虎榜明细 — Tushare top_list."""
    __tablename__ = "raw_top_list"
    __table_args__ = {"comment": "龙虎榜明细 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="股票名称"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="上榜原因"
    )
    close_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="收盘价"
    )
    pct_chg: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="涨跌幅(%)"
    )
    turnover_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="换手率(%)"
    )
    total_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="总成交额(万元)"
    )
    net_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净买入额(万元)"
    )
    buy_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="买入额(万元)"
    )
    sell_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="卖出额(万元)"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )
