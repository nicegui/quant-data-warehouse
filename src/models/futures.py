"""Futures data — 期货日线、持仓."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger
from src.models.base import TimestampMixin, Base


class RawFutDaily(TimestampMixin, Base):
    """期货日线行情 (fut_daily)."""
    __tablename__ = "raw_fut_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    pre_close = Column(Float)
    pre_settle = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    settle = Column(Float)
    change1 = Column(Float)        # 涨跌1（收盘-前收盘）
    change2 = Column(Float)        # 涨跌2（结算-前结算）
    vol = Column(Float)
    amount = Column(Float)
    oi = Column(Float)             # 持仓量
    oi_chg = Column(Float)         # 持仓量变化


class RawFutHolding(TimestampMixin, Base):
    """期货会员持仓 (fut_holding)."""
    __tablename__ = "raw_fut_holding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    symbol = Column(String(32), nullable=False)
    broker = Column(String(128), nullable=False)
    vol = Column(Float)            # 成交量
    vol_chg = Column(Float)        # 成交量变化
    long_hld = Column(Float)       # 持买仓量
    long_chg = Column(Float)
    short_hld = Column(Float)      # 持卖仓量
    short_chg = Column(Float)


class RefFutBasic(TimestampMixin, Base):
    """期货基本信息 (fut_basic).

    Source: Tushare fut_basic API
    Fields: ts_code, symbol, exchange, name, fut_code, multiplier,
            trade_unit, per_unit, quote_unit, quote_unit_desc,
            d_mode_desc, list_date, delist_date, d_month, last_ddate
    """
    __tablename__ = "ref_fut_basic"
    __table_args__ = (
        {"comment": "期货基本信息"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True, unique=True, comment="合约代码")
    symbol = Column(String(8), nullable=True, comment="品种代码")
    exchange = Column(String(8), nullable=True, comment="交易所")
    name = Column(String(64), nullable=True, comment="品种名称")
    fut_code = Column(String(8), nullable=True, comment="合约标识")
    multiplier = Column(Float, nullable=True, comment="合约乘数")
    trade_unit = Column(String(8), nullable=True, comment="交易单位")
    per_unit = Column(Float, nullable=True, comment="每跳价格")
    quote_unit = Column(String(16), nullable=True, comment="报价单位")
    quote_unit_desc = Column(String(32), nullable=True, comment="报价单位说明")
    d_mode_desc = Column(String(32), nullable=True, comment="交割方式")
    list_date = Column(String(8), nullable=True, comment="上市日期")
    delist_date = Column(String(8), nullable=True, comment="退市日期")
    d_month = Column(String(8), nullable=True, comment="交割月份")
    last_ddate = Column(String(8), nullable=True, comment="最后交割日")


class RawFutWsr(TimestampMixin, Base):
    """期货仓单 (fut_wsr).

    Source: Tushare fut_wsr API
    Fields: trade_date, symbol, fut_name, warehouse, pre_vol,
            vol, vol_chg, unit
    """
    __tablename__ = "raw_fut_wsr"
    __table_args__ = (
        {"comment": "期货仓单 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, comment="交易日期")
    symbol = Column(String(8), nullable=False, comment="品种代码")
    fut_name = Column(String(64), nullable=True, comment="品种名称")
    warehouse = Column(String(128), nullable=True, comment="仓库")
    pre_vol = Column(Float, nullable=True, comment="昨日仓单量")
    vol = Column(Float, nullable=True, comment="今日仓单量")
    vol_chg = Column(Float, nullable=True, comment="仓单变化量")
    unit = Column(String(8), nullable=True, comment="单位")


class RawFutMapping(TimestampMixin, Base):
    """主力合约映射 (fut_mapping)."""
    __tablename__ = "raw_fut_mapping"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    mapping_ts_code = Column(String(32), nullable=False)

class RawFutSettle(TimestampMixin, Base):
    """结算参数 (fut_settle)."""
    __tablename__ = "raw_fut_settle"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    settle = Column(Float)
    trading_fee_rate = Column(Float)
    trading_fee = Column(Float)
    delivery_fee = Column(Float)
    b_hedging_margin_rate = Column(Float)
    s_hedging_margin_rate = Column(Float)
    long_margin_rate = Column(Float)
    short_margin_rate = Column(Float)
