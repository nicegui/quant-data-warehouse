"""Models for 创新高 — akshare v7."""

from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import BigInteger, Date, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawStockCxg(TimestampMixin, Base):
    """创新高排名 — akshare stock_rank_cxg_ths().
    
    支持: 创月新高/半年新高/一年新高/历史新高.
    每日快照，按 (code, symbol) 去重覆盖.
    """

    __tablename__ = "raw_stock_cxg"
    __table_args__ = (
        UniqueConstraint("code", "symbol", name="uq_cxg_code_sym"),
        {"comment": "创新高排名(同花顺) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股票简称")
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="新高类型: 创月/半年/一年/历史新高")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅%")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率%")
    latest_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最新价")
    prev_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="前期高点")
    prev_high_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="前期高点日期")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
