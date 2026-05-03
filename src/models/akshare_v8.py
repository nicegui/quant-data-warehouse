"""Models for 同行比较 — akshare v8."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawPeerComparison(TimestampMixin, Base):
    """同行比较 — 东方财富 finance.eastmoney.com.
    
    4个维度: 估值比较 / 成长性比较 / 杜邦分析比较 / 公司规模.
    每条记录 = 一只股票在某个维度的同行对比行.
    去重: (target_symbol, dimension, code).
    """

    __tablename__ = "raw_peer_comparison"
    __table_args__ = (
        UniqueConstraint("target_symbol", "dimension", "code", name="uq_peer_target_dim_code"),
        {"comment": "同行比较(东方财富) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="查询的目标股票代码")
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="同行股票代码")
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股票简称")
    dimension: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="维度: valuation/growth/dupont/scale")
    rank_info: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="排名信息, 如 '9.0/21'")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
