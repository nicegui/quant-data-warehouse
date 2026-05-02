"""东方财富热榜 — dc_hot (东方财富App人气榜/飙升榜)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawDcHot(TimestampMixin, Base):
    """东方财富热榜 (dc_hot).

    Source: Tushare dc_hot API
    Fields: trade_date, data_type, ts_code, ts_name, rank,
            pct_change, current_price, rank_time, market, hot_type
    """

    __tablename__ = "raw_dc_hot"
    __table_args__ = (
        UniqueConstraint(
            "trade_date", "ts_code", "market", "hot_type", "rank_time",
            name="uq_raw_dc_hot_key",
        ),
        {"comment": "东方财富热榜 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    data_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="数据类型")
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    ts_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="股票名称")
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="排行/热度")
    pct_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅%")
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当前价")
    rank_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="排行榜获取时间")
    market: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="市场类型(A股/ETF/港股/美股)")
    hot_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="热点类型(人气榜/飙升榜)")
    hot: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="热度值")
    concept: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="所属概念")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawDcHot({self.trade_date}, {self.ts_code}, {self.market}, {self.hot_type})>"
