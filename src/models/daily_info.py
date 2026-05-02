"""Raw daily info (市场交易统计) model."""
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawDailyInfo(Base):
    __tablename__ = "raw_daily_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="板块代码")
    ts_name: Mapped[str] = mapped_column(String(64), comment="板块名称")
    com_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="挂牌数")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总股本")
    float_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通股本")
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总市值")
    float_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通市值")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="交易金额")
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量")
    trans_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="成交笔数")
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="平均市盈率")
    tr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率")
    exchange: Mapped[str] = mapped_column(String(8), comment="交易所")
