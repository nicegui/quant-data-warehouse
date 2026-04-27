"""Unified asset registry.

Every tradable entity (stock, crypto pair, index, ETF, futures)
gets a single UUID that all data tables reference.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Asset(TimestampMixin, Base):
    """Unified asset identifier."""
    __tablename__ = "asset"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_type: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True,
        comment="stock | crypto | index | fund | futures | etf"
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="ISIN (A股专用)")

    # Source-native identifier for back-ref
    source_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="e.g. 000001.SZ, BTC/USDT"
    )

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active",
        comment="active | delisted | suspended"
    )

    # SCD2 validity range
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When this record became effective"
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When this record was superseded (NULL = current)"
    )

    extra: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON blob for exchange-specific metadata"
    )

    def __repr__(self) -> str:
        return f"<Asset {self.symbol}.{self.exchange} ({self.asset_type})>"
