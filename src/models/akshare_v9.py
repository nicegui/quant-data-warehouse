"""Models for 商品/物流/糖指数 — akshare v9."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawCommodityLogistics(TimestampMixin, Base):
    """商品现货 & 物流运价/运量 & 糖指数.
    
    统一模型存储各维度数据.
    去重: (source, sub_index, date).
    """

    __tablename__ = "raw_commodity_logistics"
    __table_args__ = (
        UniqueConstraint("source", "sub_index", "date", name="uq_cl_src_sub_date"),
        {"comment": "商品/物流/糖指数(akshare v9)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="数据来源: freight/sugar/price_cflp/volume_cflp")
    sub_index: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="子指数名称")
    date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主值")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
