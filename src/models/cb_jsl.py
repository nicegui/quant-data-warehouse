"""可转债集思录数据模型 — akshare bond_cb_jsl()."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawCbJsl(TimestampMixin, Base):
    """可转债集思录实时数据 — akshare bond_cb_jsl()

    全量拉取（约30条），按 code 去重。
    """
    __tablename__ = "raw_cb_jsl"
    __table_args__ = (
        UniqueConstraint("code", name="uq_raw_cb_jsl_code"),
        {"comment": "可转债集思录实时数据 — akshare bond_cb_jsl()"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="转债代码")
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="转债名称")
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="现价")
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅")
    stock_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="正股代码")
    stock_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="正股名称")
    stock_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="正股价")
    stock_pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="正股涨跌")
    stock_pb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="正股PB")
    conv_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="转股价")
    conv_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="转股价值")
    conv_premium: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="转股溢价率")
    bond_rating: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="债券评级")
    put_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="回售触发价")
    call_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="强赎触发价")
    cb_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="转债占比")
    maturity_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="到期时间")
    remain_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="剩余年限")
    remain_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="剩余规模")
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率")
    ytm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="到期税前收益")
    dual_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="双低")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整响应JSON")
