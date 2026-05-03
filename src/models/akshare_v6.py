"""Models for IPO申报 — akshare v6."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawIpoDeclare(TimestampMixin, Base):
    """IPO申报企业 — akshare stock_ipo_declare_em()."""

    __tablename__ = "raw_ipo_declare"
    __table_args__ = (
        UniqueConstraint("company_name", name="uq_ipod_name"),
        {"comment": "IPO申报企业 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="最新状态")
    location: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="注册地")
    underwriter: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="保荐机构")
    law_firm: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="律师事务所")
    accountant: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="会计师事务所")
    market: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="拟上市地点")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
