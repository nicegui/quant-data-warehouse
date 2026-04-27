"""Pipeline audit logs for monitoring."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class PipelineLog(TimestampMixin, Base):
    """Audit log for every pipeline run."""
    __tablename__ = "pipeline_log"
    __table_args__ = (
        {"comment": "Pipeline执行日志"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pipeline_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="e.g. stock_daily, consultations"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="running | success | failed | partial"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    records_fetched: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    records_written: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_snapshot: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON of pipeline config at run time"
    )
