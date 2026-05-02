"""Raw DC concept (东方财富概念题材列表)."""
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawDcConcept(Base):
    __tablename__ = "raw_dc_concept"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    theme_code: Mapped[str] = mapped_column(String(32), index=True, comment="题材代码 (xxxxxx.DC)")
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    name: Mapped[str] = mapped_column(String(128), comment="题材名称")
    pct_change: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="涨跌幅%")
    hot: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="热度")
    sort: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="排名")
    strength: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="强度")
    z_t_num: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="涨停数量")
    main_change: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="主力净流入(元)")
    lead_stock: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="领涨股票")
    lead_stock_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="领涨股票代码")
    lead_stock_pct_change: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="领涨股票涨跌幅")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawDcConcept {self.theme_code} {self.trade_date}>"
