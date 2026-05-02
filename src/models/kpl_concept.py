"""Raw KPL concept constituents (开盘啦题材成分股)."""
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawKplConcept(Base):
    """KPL concept meta — list of all题材 codes."""

    __tablename__ = "raw_kpl_concept"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="数据日期")
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="题材代码 (xxxxxx.KP)")
    name: Mapped[str] = mapped_column(String(128), comment="题材名称")
    z_t_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="涨停数")
    up_num: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="上涨数")


class RawKplConceptCons(Base):
    """KPL concept constituents — which stocks belong to each题材."""

    __tablename__ = "raw_kpl_concept_cons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="题材代码 (xxxxxx.KP)")
    name: Mapped[str] = mapped_column(String(128), comment="题材名称")
    con_name: Mapped[str] = mapped_column(String(128), comment="股票名称")
    con_code: Mapped[str] = mapped_column(String(32), index=True, comment="股票代码")
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    hot_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="人气值")

    def __repr__(self):
        return f"<RawKplConceptCons {self.ts_code} {self.con_code} {self.trade_date}>"
