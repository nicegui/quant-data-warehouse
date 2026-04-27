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
