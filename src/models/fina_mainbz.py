"""主营业务构成 (fina_mainbz_vip)."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin

class RawFinaMainbz(TimestampMixin, Base):
    __tablename__ = "raw_fina_mainbz"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "bz_item", "type", name="uq_fmb_ts_end_item_type"),
        {"comment": "主营业务构成 — fina_mainbz_vip"},
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(nullable=False, index=True)
    bz_item: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="主营业务来源")
    bz_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bz_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bz_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    curr_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="P/D/I")
    update_flag: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
