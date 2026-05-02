"""东方财富板块日线行情 — RawDcDaily

Source: Tushare dc_daily API
Fields: ts_code, trade_date, close, open, high, low, change, pct_change,
        vol, amount, swing, turnover_rate, category
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawDcDaily(TimestampMixin, Base):
    """东方财富板块日线 (dc_daily).

    Source: Tushare dc_daily API
    """
    __tablename__ = "raw_dc_daily"
    __table_args__ = (
        {"comment": "东方财富板块日线 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="板块代码")
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True, comment="交易日")
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌点位")
    pct_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅")
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量(股)")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额(元)")
    swing: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="振幅")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率")
    category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="板块类型")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始JSON")
