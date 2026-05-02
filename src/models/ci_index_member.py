"""Raw CI index member (中信行业成分) model."""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawCiIndexMember(Base):
    __tablename__ = "raw_ci_index_member"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    l1_code: Mapped[str] = mapped_column(String(32), index=True, comment="一级行业代码")
    l1_name: Mapped[str] = mapped_column(String(128), comment="一级行业名称")
    l2_code: Mapped[str] = mapped_column(String(32), index=True, comment="二级行业代码")
    l2_name: Mapped[str] = mapped_column(String(128), comment="二级行业名称")
    l3_code: Mapped[str] = mapped_column(String(32), index=True, comment="三级行业代码")
    l3_name: Mapped[str] = mapped_column(String(128), comment="三级行业名称")
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="成分股票代码")
    name: Mapped[str] = mapped_column(String(128), comment="成分股票名称")
    in_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="纳入日期")
    out_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="剔除日期")
    is_new: Mapped[Optional[str]] = mapped_column(String(4), nullable=True, comment="是否最新")
