"""指数成分股快照 — akshare index_stock_cons_csindex()."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawIndexCons(TimestampMixin, Base):
    """指数成分股 — akshare index_stock_cons_csindex(symbol=...).

    Supported symbols: "000300"(沪深300), "000905"(中证500), "000016"(上证50),
    "399006"(创业板指), etc.
    """

    __tablename__ = "raw_index_cons"
    __table_args__ = (
        UniqueConstraint(
            "index_code", "stock_code", "snapshot_date",
            name="uq_index_cons_idx_stock_date",
        ),
        {"comment": "指数成分股快照 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    index_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="指数代码"
    )
    index_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="指数名称"
    )
    index_name_en: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="指数英文名称"
    )
    stock_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="成分券代码"
    )
    stock_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="成分券名称"
    )
    stock_name_en: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="成分券英文名称"
    )
    exchange: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="交易所"
    )
    exchange_en: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="交易所英文名称"
    )
    snapshot_date: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="快照日期"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整响应JSON"
    )

    def __repr__(self):
        return (
            f"<RawIndexCons({self.index_code}, {self.stock_code}, "
            f"{self.snapshot_date})>"
        )
