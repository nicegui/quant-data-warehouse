"""Raw research report (券商研究报告) model."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawResearchReport(Base):
    __tablename__ = "raw_research_report"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="研报发布时间")
    title: Mapped[str] = mapped_column(Text, comment="研报标题")
    report_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="研报类别")
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="作者")
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="股票名称")
    ts_code: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True, comment="股票代码")
    inst_csname: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True, comment="机构简称")
    ind_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="行业名称")
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="下载链接")
