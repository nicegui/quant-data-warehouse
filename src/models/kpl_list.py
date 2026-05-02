"""Raw KPL list (开盘啦榜单) — 涨停/炸板/跌停/自然涨停/竞价."""
from sqlalchemy import String, Float, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base

class RawKplList(Base):
    __tablename__ = "raw_kpl_list"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), index=True, comment="股票代码")
    name: Mapped[str] = mapped_column(String(64), comment="股票名称")
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    lu_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="涨停时间")
    ld_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="跌停时间")
    open_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="开板时间")
    last_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="最后涨停时间")
    lu_desc: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="涨停原因")
    tag: Mapped[str] = mapped_column(String(32), index=True, comment="标签(涨停/炸板/跌停/自然涨停/竞价)")
    theme: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="所属板块")
    net_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主力净额(元)")
    bid_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="竞价成交额(元)")
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="状态(N连板)")
    bid_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="竞价净额")
    bid_turnover: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="竞价换手%")
    lu_bid_vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨停委买额")
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅%")
    bid_pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="竞价涨幅%")
    rt_pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="实时涨幅%")
    limit_order: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="封单")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率%")
    free_float: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="实际流通")
    lu_limit_order: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最大封单")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawKplList {self.ts_code} {self.trade_date} {self.tag}>"
