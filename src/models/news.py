"""News and consultation data.""" 

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawConsultation(TimestampMixin, Base):
    """Tushare news — raw API response, append-only.

    Fields from API: datetime, content, title
    """
    __tablename__ = "raw_consultation"
    __table_args__ = (
        {"comment": "快讯咨询 — 原始数据，以datetime为唯一标识"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    datetime: Mapped[str] = mapped_column(String(19), nullable=False, unique=True, comment="发布时间 YYYY-MM-DD HH:MM:SS")
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawMajorNews(TimestampMixin, Base):
    """Tushare major_news — raw API response.

    Fields from API: title, pub_time, src, url
    """
    __tablename__ = "raw_major_news"
    __table_args__ = (
        {"comment": "重大新闻 — 原始数据"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    pub_time: Mapped[str] = mapped_column(String(19), nullable=False, index=True, comment="发布时间")
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="来源")
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawCctvNews(TimestampMixin, Base):
    """新闻联播 (cctv_news).

    Source: Tushare cctv_news API
    Fields: date, title, content
    """
    __tablename__ = "raw_cctv_news"
    __table_args__ = (
        {"comment": "新闻联播 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), nullable=False, index=True, comment="新闻日期")
    title: Mapped[str] = mapped_column(String(512), nullable=False, comment="新闻标题")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="新闻内容")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
