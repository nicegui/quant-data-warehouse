"""审计意见 (fina_audit_vip)."""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin

class RawFinaAudit(TimestampMixin, Base):
    __tablename__ = "raw_fina_audit"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", name="uq_fa_ts_end"),
        {"comment": "财务审计意见 — fina_audit_vip"},
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[datetime] = mapped_column(nullable=False, index=True)
    audit_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="审计结果")
    audit_fees: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="审计总费用")
    audit_agency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="会计事务所")
    audit_sign: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="签字会计师")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
