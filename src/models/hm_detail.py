"""游资每日明细 — RawHmDetail

Source: Tushare hm_detail API
Fields: trade_date, ts_code, ts_name, buy_amount, sell_amount,
        net_amount, hm_name, hm_orgs, tag
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawHmDetail(TimestampMixin, Base):
    """游资每日明细 (hm_detail)."""
    __tablename__ = "raw_hm_detail"
    __table_args__ = ({"comment": "游资每日明细 — 原始数据"},)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True, comment="交易日期")
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="股票代码")
    ts_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="股票名称")
    buy_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="买入金额")
    sell_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="卖出金额")
    net_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净买卖")
    hm_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="游资名称")
    hm_orgs: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="关联机构")
    tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="标签")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始JSON")
