"""个股资金流模型 — akshare stock_individual_fund_flow()."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawFundFlow(TimestampMixin, Base):
    """个股资金流 — akshare stock_individual_fund_flow(stock, market)

    逐股按日拉取（~120条/股），按 (stock_code, trade_date) 去重。
    """

    __tablename__ = "raw_fund_flow"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", name="uq_fund_flow_stock_date"),
        {"comment": "个股资金流 — akshare stock_individual_fund_flow()"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="交易日")

    # 行情
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收盘价")
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅")

    # 主力净流入
    main_net: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主力净流入-净额")
    main_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主力净流入-净占比")

    # 超大单净流入
    super_large_net: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="超大单净流入-净额")
    super_large_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="超大单净流入-净占比")

    # 大单净流入
    large_net: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="大单净流入-净额")
    large_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="大单净流入-净占比")

    # 中单净流入
    medium_net: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="中单净流入-净额")
    medium_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="中单净流入-净占比")

    # 小单净流入
    small_net: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="小单净流入-净额")
    small_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="小单净流入-净占比")

    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
