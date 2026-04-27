"""News and consultation data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawConsultation(TimestampMixin, Base):
    """Tushare news/consultation — raw API response, append-only."""
    __tablename__ = "raw_consultation"
    __table_args__ = (
        {"comment": "快讯咨询 — 原始数据"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    news_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="资讯ID")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="来源")
    pub_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawMajorNews(TimestampMixin, Base):
    """Tushare major_news — raw API response, append-only."""
    __tablename__ = "raw_major_news"
    __table_args__ = (
        {"comment": "重大新闻 — 原始数据"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    news_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pub_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    impact_level: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="impact level"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
