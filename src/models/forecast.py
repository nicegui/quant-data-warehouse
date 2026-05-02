"""业绩预告 (forecast_vip) — 全量 VIP 接口."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawForecast(TimestampMixin, Base):
    """业绩预告 — 全量 VIP (forecast_vip)."""

    __tablename__ = "raw_forecast"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", name="uq_fc_ts_end"),
        {"comment": "业绩预告 — forecast_vip 全量"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[datetime] = mapped_column(nullable=False, index=True, comment="报告期")
    type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="预告类型")
    p_change_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润变动幅度下限(%)")
    p_change_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润变动幅度上限(%)")
    net_profit_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预告净利润下限(万)")
    net_profit_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预告净利润上限(万)")
    last_parent_net: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="上年同期归属母公司净利润")
    first_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="首次公告日")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="业绩预告摘要")
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="业绩变动原因")

    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应")

    def __repr__(self):
        return f"<RawForecast({self.ts_code} {self.end_date:%Y%m%d} {self.type})>"
