"""Index / sector / concept — 指数日线、申万板块、概念板块."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger
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
