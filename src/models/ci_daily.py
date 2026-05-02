"""Raw CI daily (中信行业指数行情) model."""
from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawCiDaily(Base):
    __tablename__ = "raw_ci_daily"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="指数代码")
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
