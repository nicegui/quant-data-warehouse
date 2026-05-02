"""Raw DC concept constituents (东方财富题材成分)."""
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawDcConceptCons(Base):
    __tablename__ = "raw_dc_concept_cons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="股票代码")
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    name: Mapped[str] = mapped_column(String(128), comment="股票名称")
    theme_code: Mapped[str] = mapped_column(String(32), index=True, comment="题材代码")
    industry_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="行业代码")
    industry: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="所属行业")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="入选原因")
    hot_num: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="热点排行")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawDcConceptCons {self.ts_code} {self.theme_code} {self.trade_date}>"
