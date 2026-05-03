"""Models for 分析师一致预期 — Eastmoney profit forecast snapshot."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawAnalystForecast(TimestampMixin, Base):
    """分析师一致预期快照 — Eastmoney RPT_WEB_RESPREDICT.

    Snapshot of analyst consensus: ratings, EPS forecasts, target prices.
    Each run stores a full snapshot keyed by (stock_code, snapshot_date).
    """

    __tablename__ = "raw_analyst_forecast"
    __table_args__ = (
        UniqueConstraint("stock_code", "snapshot_date", name="uq_af_code_date"),
        {"comment": "分析师一致预期 — Eastmoney snapshot"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码 (600519.SH)")
    stock_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="股票名称")
    snapshot_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="快照日期")
    # Ratings
    rating_org_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="覆盖机构数")
    rating_buy_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="买入评级数")
    rating_add_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="增持评级数")
    rating_neutral_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="中性评级数")
    rating_reduce_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="减持评级数")
    rating_sale_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="卖出评级数")
    # EPS forecasts
    year1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="预测年份1")
    eps1: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预测EPS1")
    year2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="预测年份2")
    eps2: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预测EPS2")
    year3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="预测年份3")
    eps3: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预测EPS3")
    # Target price
    aim_price_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="目标价上限")
    aim_price_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="目标价下限")
    # Industry
    industry: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="东方财富行业")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
