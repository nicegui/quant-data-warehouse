"""大宗商品指数 — dc_index (东方财富概念/行业板块指数)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawDcIndex(TimestampMixin, Base):
    """大宗商品指数 (dc_index).

    Source: Tushare dc_index API
    Fields: ts_code, trade_date, name, leading, leading_code, pct_change,
            leading_pct, total_mv, turnover_rate, up_num, down_num, idx_type, level
    """
    __tablename__ = "raw_dc_index"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_dc_index_code_date"),
        {"comment": "大宗商品指数 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="指数名称")
    leading: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="领涨品种")
    leading_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="领涨品种代码")
    pct_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="板块涨跌幅(%)")
    leading_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="领涨品种涨跌幅(%)")
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="板块总市值(万元)")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率(%)")
    up_num: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="上涨家数")
    down_num: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="下跌家数")
    idx_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="指数类型")
    level: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="层级")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawDcIndex({self.ts_code}, {self.trade_date})>"
