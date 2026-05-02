"""游资名录 — RawHmList

Source: Tushare hm_list API
Fields: name, desc, orgs
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawHmList(TimestampMixin, Base):
    """游资名录 (hm_list)."""
    __tablename__ = "raw_hm_list"
    __table_args__ = ({"comment": "游资名录 — 原始数据"},)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="游资名称")
    desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="说明")
    orgs: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="关联机构JSON")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始JSON")
