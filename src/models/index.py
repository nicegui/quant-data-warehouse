"""Index / sector / concept — 指数日线、申万板块、概念板块."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, String, Float, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import TimestampMixin, Base


class RawIndexDaily(TimestampMixin, Base):
    """指数日线行情 (index_daily)."""
    __tablename__ = "raw_index_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)


class RawSwDaily(TimestampMixin, Base):
    """申万行业指数日线 (sw_daily)."""
    __tablename__ = "raw_sw_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)


class RefConcept(TimestampMixin, Base):
    """概念板块列表 (concept)."""
    __tablename__ = "ref_concept"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(128))
    src = Column(String(16))        # ts / ths


class RefConceptDetail(TimestampMixin, Base):
    """概念板块成分股 (concept_detail / ths_member)."""
    __tablename__ = "ref_concept_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    concept_code = Column(String(32), nullable=False, index=True)
    concept_name = Column(String(128))
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64))
    weight = Column(Float)           # 权重


class RawIndexWeight(TimestampMixin, Base):
    """指数成分权重 (index_weight).

    Source: Tushare index_weight API
    Monthly weight data for each constituent stock in a given index.
    """
    __tablename__ = "raw_index_weight"
    __table_args__ = (
        {"comment": "指数成分权重 — 月度数据"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    index_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    con_code: Mapped[str] = mapped_column(String(16), nullable=False, comment="成分股代码")
    trade_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="权重日期"
    )
    weight: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="权重(%)"
    )

    def __repr__(self):
        return f"<RawIndexWeight({self.index_code}, {self.con_code}, {self.trade_date})>"


class RefIndexBasic(TimestampMixin, Base):
    """指数基本信息 (index_basic).

    Reference data — full pull, no checkpoint.
    Tushare pro.index_basic(market=...).
    """
    __tablename__ = "ref_index_basic"
    __table_args__ = (
        {"comment": "指数基本信息 — 参考数据，全量更新"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True, unique=True, comment="指数代码")
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="指数名称")
    market: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="市场")
    publisher: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="发布机构")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="指数类别")
    base_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="基期")
    base_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="基点")
    list_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="发布日期")
    exp_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="终止日期")
    fullname: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="指数全称")
    index_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="指数类型")
    weight_rule: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="加权方式")
    desc: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="指数描述")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RefIndexBasic({self.ts_code}, {self.name})>"
