"""Macroeconomic data — CPI/PMI/GDP/M2/Shibor."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger
from src.models.base import TimestampMixin, Base


class RawCnCpi(TimestampMixin, Base):
    """居民消费价格指数 (cn_cpi)."""
    __tablename__ = "raw_cn_cpi"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(String(8), nullable=False, index=True, unique=True)
    nt_val = Column(Float)         # 全国当月值
    nt_yoy = Column(Float)         # 全国同比（%）
    nt_mom = Column(Float)         # 全国环比（%）
    nt_accu = Column(Float)        # 全国累计（%）


class RawCnPmi(TimestampMixin, Base):
    """采购经理人指数 (cn_pmi)."""
    __tablename__ = "raw_cn_pmi"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(String(8), nullable=False, index=True, unique=True)
    pmi = Column(Float)            # PMI
    pmi_yoy = Column(Float)        # 同比
    pmi_month = Column(Float)      # 环比


class RawCnGdp(TimestampMixin, Base):
    """国内生产总值 (cn_gdp)."""
    __tablename__ = "raw_cn_gdp"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quarter = Column(String(8), nullable=False, index=True, unique=True)
    gdp = Column(Float)            # GDP（亿元）
    gdp_yoy = Column(Float)        # 同比增速（%）
    pi = Column(Float)             # 第一产业
    pi_yoy = Column(Float)
    si = Column(Float)             # 第二产业
    si_yoy = Column(Float)
    ti = Column(Float)             # 第三产业
    ti_yoy = Column(Float)


class RawCnMoneySupply(TimestampMixin, Base):
    """货币供应量 (cn_m)."""
    __tablename__ = "raw_cn_money_supply"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(String(8), nullable=False, index=True, unique=True)
    m0 = Column(Float)             # M0（亿元）
    m0_yoy = Column(Float)         # M0同比
    m1 = Column(Float)
    m1_yoy = Column(Float)
    m2 = Column(Float)
    m2_yoy = Column(Float)


class RawShibor(TimestampMixin, Base):
    """上海银行间同业拆放利率 (shibor)."""
    __tablename__ = "raw_shibor"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(String(8), nullable=False, index=True)
    on_rate = Column(Float)        # 隔夜
    on_bid = Column(Float)         # 隔夜买价
    w1_rate = Column(Float)
    w1_bid = Column(Float)
    w2_rate = Column(Float)
    w2_bid = Column(Float)         # 2周买价
    m1_rate = Column(Float)
    m3_rate = Column(Float)
    m6_rate = Column(Float)
    m9_rate = Column(Float)
    y1_rate = Column(Float)
