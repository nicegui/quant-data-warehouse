"""Raw index factor pro (指数技术因子) model."""
import json
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.models.base import Base


class RawIdxFactorPro(Base):
    __tablename__ = "raw_idx_factor_pro"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), index=True, comment="指数代码")
    trade_date: Mapped[str] = mapped_column(String(10), index=True, comment="交易日期")
    raw_json: Mapped[str] = mapped_column(Text, comment="完整89列API响应JSON")
