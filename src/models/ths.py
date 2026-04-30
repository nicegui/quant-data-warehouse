"""同花顺概念板块 (ths_daily + ths_hot)."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger, Text
from src.models.base import TimestampMixin, Base


class RawThsDaily(TimestampMixin, Base):
    """同花顺概念板块日线行情 (ths_daily).

    Source: Tushare ths_daily API
    Fields: ts_code, trade_date, open, high, low, close, pre_close,
            avg_price, change, pct_change, vol, turnover_rate
    """
    __tablename__ = "raw_ths_daily"
    __table_args__ = (
        {"comment": "同花顺概念板块日线 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True, comment="板块代码")
    trade_date = Column(String(8), nullable=False, index=True, comment="交易日期")
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    pre_close = Column(Float, nullable=True)
    avg_price = Column(Float, nullable=True, comment="均价")
    change = Column(Float, nullable=True, comment="涨跌额")
    pct_change = Column(Float, nullable=True, comment="涨跌幅(%)")
    vol = Column(Float, nullable=True, comment="成交量(手)")
    turnover_rate = Column(Float, nullable=True, comment="换手率(%)")


class RawThsHot(TimestampMixin, Base):
    """同花顺热榜 (ths_hot).

    Source: Tushare ths_hot API
    Fields: trade_date, data_type, ts_code, ts_name, rank, pct_change,
            current_price, hot, concept, rank_time, rank_reason
    """
    __tablename__ = "raw_ths_hot"
    __table_args__ = (
        {"comment": "同花顺热榜 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, comment="交易日期")
    data_type = Column(String(8), nullable=True, comment="数据类型: 期货/港股/A股")
    ts_code = Column(String(32), nullable=False, index=True, comment="代码")
    ts_name = Column(String(128), nullable=True, comment="名称")
    rank = Column(Float, nullable=True, comment="排名")
    pct_change = Column(Float, nullable=True, comment="涨跌幅(%)")
    current_price = Column(Float, nullable=True, comment="当前价")
    hot = Column(Float, nullable=True, comment="热度")
    concept = Column(String(256), nullable=True, comment="概念标签")
    rank_time = Column(String(32), nullable=True, comment="排行时间")
    rank_reason = Column(Text, nullable=True, comment="上榜原因")
