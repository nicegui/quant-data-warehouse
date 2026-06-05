"""Polymarket prediction market data models.

Three tables:
  - raw_polymarket_events:   Event metadata (title, volume, category)
  - raw_polymarket_markets:  Individual markets (question, outcomes, prices)
  - raw_polymarket_prices:   Price time series (probability history)

Source: Polymarket public REST APIs (gamma-api, clob, data-api)
Dedup: events by id, markets by condition_id, prices by (condition_id, timestamp)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawPolymarketEvent(TimestampMixin, Base):
    """Polymarket event — groups related markets under one topic."""

    __tablename__ = "raw_polymarket_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_pm_event_id"),
        {"comment": "Polymarket事件元数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="Gamma API event id")
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="事件标题")
    slug: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="URL slug")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="事件描述")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="分类标签")
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="标签JSON数组")
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="累计成交量(USDC)")
    liquidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动性(USDC)")
    active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, comment="是否活跃")
    closed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, comment="是否已结算")
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="开始时间")
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始JSON")


class RawPolymarketMarket(TimestampMixin, Base):
    """Polymarket market — binary outcome question with prices."""

    __tablename__ = "raw_polymarket_markets"
    __table_args__ = (
        UniqueConstraint("condition_id", name="uq_pm_condition_id"),
        {"comment": "Polymarket市场(二元问题)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    condition_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="CLOB condition ID (0x...)")
    event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="关联事件ID")
    question: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="市场问题")
    slug: Mapped[Optional[str]] = mapped_column(String(300), nullable=True, comment="URL slug")
    outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="结果JSON数组 e.g. ['Yes','No']")
    outcome_prices: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="当前价格JSON数组 e.g. ['0.65','0.35']")
    clob_token_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="CLOB token ID JSON数组")
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量(USDC)")
    liquidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动性(USDC)")
    active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, comment="是否活跃")
    closed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, comment="是否已结算")
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结算时间")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="分类")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始JSON")


class RawPolymarketPrice(TimestampMixin, Base):
    """Polymarket price history — probability time series for each market."""

    __tablename__ = "raw_polymarket_prices"
    __table_args__ = (
        UniqueConstraint("condition_id", "timestamp", name="uq_pm_price_condition_ts"),
        {"comment": "Polymarket价格历史(概率时间序列)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    condition_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="市场condition ID")
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="数据点时间")
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="概率价格(0-1)")
