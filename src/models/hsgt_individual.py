"""Models for 北向资金个股持股明细 — akshare stock_hsgt_individual_em()."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawHsgtIndividual(TimestampMixin, Base):
    """北向资金个股持股明细 — akshare stock_hsgt_individual_em(symbol=...).

    Each row is one day's northbound holding data for a single stock.
    Dedup key: (stock_code, trade_date).
    """

    __tablename__ = "raw_hsgt_individual"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", name="uq_hsgt_ind_code_date"),
        {"comment": "北向资金个股持股明细 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="持股日期")
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当日收盘价")
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="当日涨跌幅")
    hold_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股数量")
    hold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股市值")
    hold_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股数量占A股百分比")
    delta_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="今日增持股数")
    delta_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="今日增持资金")
    delta_market_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="今日持股市值变化")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
