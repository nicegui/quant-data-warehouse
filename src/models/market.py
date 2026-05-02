"""Market data models — raw (append-only) and curated (adjusted).

- Raw layer: direct API dump, never modified
- Curated layer: cleaned, forward-adjusted (前复权)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


# ──────────────────────────────────────────
#  RAW LAYER (append-only)
# ──────────────────────────────────────────

class RawStockDaily(TimestampMixin, Base):
    """A-share daily OHLCV — raw API response, immutable."""
    __tablename__ = "raw_stock_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_stock_daily_code_date"),
        {"comment": "A股日线 — 原始API返回，不可变"},
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
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStockWeekly(TimestampMixin, Base):
    """A-share weekly OHLCV — raw API response, immutable."""
    __tablename__ = "raw_stock_weekly"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_stock_weekly_code_date"),
        {"comment": "A股周线 — 原始API返回，不可变"},
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
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStockMonthly(TimestampMixin, Base):
    """A-share monthly OHLCV — raw API response, immutable."""
    __tablename__ = "raw_stock_monthly"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_stock_monthly_code_date"),
        {"comment": "A股月线 — 原始API返回，不可变"},
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
        String, nullable=True, comment="完整API响应JSON"
    )


class RawCryptoOhlcv(TimestampMixin, Base):
    """Crypto OHLCV — raw API response, immutable."""
    __tablename__ = "raw_crypto_ohlcv"
    __table_args__ = (
        {"comment": "加密币K线 — 原始API返回，不可变"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    timeframe: Mapped[str] = mapped_column(
        String(8), nullable=False, comment="1d | 4h | 1h"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


# ──────────────────────────────────────────
#  CURATED LAYER (SCD2 with forward adjustment)
# ──────────────────────────────────────────

class CuratedStockDailyAdj(TimestampMixin, Base):
    """A-share daily OHLCV — forward-adjusted (前复权)."""
    __tablename__ = "curated_stock_daily_adj"
    __table_args__ = (
        {"comment": "A股日线 — 前复权清洗数据，SCD2版本管理"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open_adj: Mapped[float] = mapped_column(Float, nullable=False)
    high_adj: Mapped[float] = mapped_column(Float, nullable=False)
    low_adj: Mapped[float] = mapped_column(Float, nullable=False)
    close_adj: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(手)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(千元)")
    adj_factor: Mapped[float] = mapped_column(
        Float, nullable=False, comment="当日前复权因子"
    )

    # SCD2 validity (data revisions, e.g. after an ex-dividend)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    version: Mapped[int] = mapped_column(
        default=1, comment="Data revision version"
    )


class CuratedCryptoOhlcv(TimestampMixin, Base):
    """Crypto OHLCV — cleaned data."""
    __tablename__ = "curated_crypto_ohlcv"
    __table_args__ = (
        {"comment": "加密币K线 — 清洗数据"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)


# ──────────────────────────────────────────
#  DAILY BASIC (每日基本面指标)
# ──────────────────────────────────────────

class RawDailyBasic(TimestampMixin, Base):
    """A-share daily basic data — PE, PB, turnover rate, market cap, etc.

    Source: Tushare daily_basic API
    API fields: ts_code, trade_date, close, turnover_rate, turnover_rate_f,
                volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
                total_share, float_share, free_share, total_mv, circ_mv
    """
    __tablename__ = "raw_daily_basic"
    __table_args__ = (
        {"comment": "A股每日基本面指标 — PE/PB/换手率/市值"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    close: Mapped[float] = mapped_column(Float, nullable=False, comment="收盘价")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率(%)")
    turnover_rate_f: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="自由流通股换手率(%)")
    volume_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="量比")
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市盈率(静态)")
    pe_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市盈率(TTM)")
    pb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市净率")
    ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市销率")
    ps_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市销率(TTM)")
    dv_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股息率(%)")
    dv_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股息率(TTM)")
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总市值(万元)")
    circ_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通市值(万元)")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总股本(万股)")
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通股本(万股)")
    free_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="自由流通股本(万股)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStkMins(TimestampMixin, Base):
    """股票分钟行情 (stk_mins).

    Source: Tushare stk_mins API
    1-min / 5-min / 15-min / 30-min / 60-min bars.
    Rate-limited at 2 calls/min — pull selectively.
    """
    __tablename__ = "raw_stk_mins"
    __table_args__ = (
        {"comment": "股票分钟行情 — 5min K线，2次/分钟限流"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_time: Mapped[Optional[str]] = mapped_column(
        String(19), nullable=True, index=True, comment="交易时间 YYYY-MM-DD HH:MM:SS"
    )
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额")

    def __repr__(self):
        return f"<RawStkMins({self.ts_code}, {self.trade_time})>"


class RawStkFactor(TimestampMixin, Base):
    """股票因子 (stk_factor) — OHLCV + 复权价 + 技术指标.

    Source: Tushare stk_factor API
    Fields: ts_code, trade_date, close, open, high, low, pre_close,
            change, pct_change, vol, amount, adj_factor,
            open_hfq, open_qfq, close_hfq, close_qfq, high_hfq, high_qfq,
            low_hfq, low_qfq, pre_close_hfq, pre_close_qfq,
            macd_dif, macd_dea, macd, kdj_k, kdj_d, kdj_j,
            rsi_6, rsi_12, rsi_24, boll_upper, boll_mid, boll_lower, cci
    """
    __tablename__ = "raw_stk_factor"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_stk_factor_code_date"),
        {"comment": "股票因子 — OHLCV + 复权价 + 技术指标"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # OHLCV
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    pre_close: Mapped[float] = mapped_column(Float, nullable=False)
    change: Mapped[float] = mapped_column(Float, nullable=False)
    pct_change: Mapped[float] = mapped_column(Float, nullable=False, comment="涨跌幅(%)")
    vol: Mapped[float] = mapped_column(Float, nullable=False, comment="成交量(手)")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额(千元)")
    adj_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="复权因子")
    # 后复权价
    open_hfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="开盘价(后复权)")
    open_qfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="开盘价(前复权)")
    close_hfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收盘价(后复权)")
    close_qfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收盘价(前复权)")
    high_hfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最高价(后复权)")
    high_qfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最高价(前复权)")
    low_hfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最低价(后复权)")
    low_qfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最低价(前复权)")
    pre_close_hfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="昨收价(后复权)")
    pre_close_qfq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="昨收价(前复权)")
    # 技术指标
    macd_dif: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="MACD DIF")
    macd_dea: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="MACD DEA")
    macd: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="MACD柱")
    kdj_k: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="KDJ K")
    kdj_d: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="KDJ D")
    kdj_j: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="KDJ J")
    rsi_6: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="RSI 6日")
    rsi_12: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="RSI 12日")
    rsi_24: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="RSI 24日")
    boll_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="BOLL上轨")
    boll_mid: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="BOLL中轨")
    boll_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="BOLL下轨")
    cci: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="CCI")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawBlockTrade(TimestampMixin, Base):
    """大宗交易 (block_trade).

    Source: Tushare block_trade API
    Fields: ts_code, trade_date, price, vol, amount, buyer, seller
    """
    __tablename__ = "raw_block_trade"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", "buyer", "seller",
                         name="uq_raw_block_trade_code_date_buyer_seller"),
        {"comment": "大宗交易 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交价")
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量(万股)")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额(万元)")
    buyer: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="买方营业部")
    seller: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="卖方营业部")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStkHolderNumber(TimestampMixin, Base):
    """股东户数 (stk_holdernumber).

    Source: Tushare stk_holdernumber API
    Fields: ts_code, ann_date, end_date, holder_num
    """
    __tablename__ = "raw_stk_holder_number"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", name="uq_raw_stk_holder_number_code_date"),
        {"comment": "股东户数 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告期")
    holder_num: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股东户数")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStkAccount(TimestampMixin, Base):
    """股票开户数 (stk_account).

    Source: Tushare stk_account API
    Fields: date, weekly_new, total, weekly_hold, weekly_trade
    """
    __tablename__ = "raw_stk_account"
    __table_args__ = (
        {"comment": "股票开户数 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True, comment="统计日期(YYYYMM)")
    weekly_new: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="本周新增(户)")
    total: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期末总户数(户)")
    weekly_hold: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="本周持仓户数(户)")
    weekly_trade: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="本周交易户数(户)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawShareFloat(TimestampMixin, Base):
    """限售股解禁 (share_float).

    Source: Tushare share_float API
    Fields: ts_code, ann_date, float_date, float_share,
            float_ratio, holder_name, share_type
    """
    __tablename__ = "raw_share_float"
    __table_args__ = (
        {"comment": "限售股解禁 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    float_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="解禁日期")
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="解禁数量(股)")
    float_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="解禁比例(%)")
    holder_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="股东名称")
    share_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="股份类型")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )

class RawStkAuction(TimestampMixin, Base):
    """盘前集合竞价 (stk_auction)."""
    __tablename__ = "raw_stk_auction"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawIndexDailyBasic(TimestampMixin, Base):
    """大盘指数每日指标 (index_dailybasic)."""
    __tablename__ = "raw_index_dailybasic"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    float_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_rate_f: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pe_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawIndexGlobal(TimestampMixin, Base):
    """全球指数行情 (index_global)."""
    __tablename__ = "raw_index_global"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    swing: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawLimitListAll(TimestampMixin, Base):
    """涨跌停列表全量 (limit_list)."""
    __tablename__ = "raw_limit_list_all"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fc_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fl_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fd_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    first_time: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    last_time: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    open_times: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    strth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    limit: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)

class RawIndexMonthly(TimestampMixin, Base):
    """指数月线 (index_monthly)."""
    __tablename__ = "raw_index_monthly"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class RawIndexWeekly(TimestampMixin, Base):
    """指数周线 (index_weekly)."""
    __tablename__ = "raw_index_weekly"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RawBakDaily(TimestampMixin, Base):
    """备用行情 (bak_daily).

    Source: Tushare bak_daily API
    Dedup: (ts_code, trade_date)
    """
    __tablename__ = "raw_bak_daily"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_bak_daily_code_date"),
        {"comment": "备用行情 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股票名称")
    pct_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turn_over: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率(%)")
    swing: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="振幅(%)")
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    selling: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    buying: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="行业")
    area: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="地区")
    float_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通市值")
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总市值")
    avg_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    strength: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    activity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_turnover: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    attack: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    interval_3: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="3日强度")
    interval_6: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="6日强度")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )


class RawStkAccountOld(TimestampMixin, Base):
    """旧版股票开户数 (stk_account_old).

    Source: Tushare stk_account_old API — 历史开户数（周度汇总）
    Dedup: date (格式: YYYYMMDD~MMDD)
    """
    __tablename__ = "raw_stk_account_old"
    __table_args__ = (
        {"comment": "旧版股票开户数(周度) — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True, comment="统计周期(YYYYMMDD~MMDD)")
    new_sh: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="沪市新增户数")
    new_sz: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="深市新增户数")
    active_sh: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="沪市活跃户数(万)")
    active_sz: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="深市活跃户数(万)")
    total_sh: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="沪市总户数(万)")
    total_sz: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="深市总户数(万)")
    trade_sh: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="沪市交易户数(万)")
    trade_sz: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="深市交易户数(万)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="完整API响应JSON"
    )
