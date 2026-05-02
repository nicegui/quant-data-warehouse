"""同花顺概念板块 (ths_member + ths_hot)."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger, Text
from src.models.base import TimestampMixin, Base


class RawThsMember(TimestampMixin, Base):
    """同花顺概念板块成分 (ths_member).

    Source: Tushare ths_member API
    Fields: ts_code, con_code, con_name, weight, in_date, out_date, is_new
    """
    __tablename__ = "raw_ths_member"
    __table_args__ = (
        {"comment": "同花顺概念板块成分 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True, comment="板块指数代码")
    con_code = Column(String(32), nullable=False, index=True, comment="股票代码")
    con_name = Column(String(128), nullable=True, comment="股票名称")
    weight = Column(Float, nullable=True, comment="权重(暂无)")
    in_date = Column(String(8), nullable=True, comment="纳入日期(暂无)")
    out_date = Column(String(8), nullable=True, comment="剔除日期(暂无)")
    is_new = Column(String(4), nullable=True, comment="是否最新Y是N否")
    raw_json = Column(Text, nullable=True, comment="原始JSON")


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
