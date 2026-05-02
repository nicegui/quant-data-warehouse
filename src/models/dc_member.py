"""东方财富板块成分 — RawDcMember

Source: Tushare dc_member API
Fields: trade_date, ts_code, con_code, name
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawDcMember(TimestampMixin, Base):
    """东方财富板块成分 (dc_member).

    Source: Tushare dc_member API
    Fields: trade_date, ts_code, con_code, name
    """
    __tablename__ = "raw_dc_member"
    __table_args__ = (
        {"comment": "东方财富板块成分 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True, comment="交易日期")
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="板块指数代码")
    con_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="成分股票代码")
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="成分股名称")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始JSON")

    def __repr__(self):
        return f"<RawDcMember({self.trade_date}, {self.ts_code}, {self.con_code})>"
