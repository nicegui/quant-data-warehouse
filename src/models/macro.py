"""Macroeconomic data — CPI/PMI/GDP/M2/Shibor."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger, Text, UniqueConstraint
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


class RawCnPpi(TimestampMixin, Base):
    """工业品出厂价格指数 (cn_ppi).

    Tushare pro.cn_ppi(start_period=..., end_period=...).
    """
    __tablename__ = "raw_cn_ppi"
    __table_args__ = (
        {"comment": "工业品出厂价格指数 PPI"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(String(8), nullable=False, index=True, unique=True, comment="月份")
    ppi_yoy = Column(Float, nullable=True, comment="PPI同比(%)")
    ppi_mp_yoy = Column(Float, nullable=True, comment="生产资料同比(%)")
    ppi_rm_yoy = Column(Float, nullable=True, comment="原材料同比(%)")
    ppi_living_yoy = Column(Float, nullable=True, comment="生活资料同比(%)")
    ppi_cg_yoy = Column(Float, nullable=True, comment="消费品同比(%)")
    ppi_mp_mom = Column(Float, nullable=True, comment="生产资料环比(%)")
    ppi_rm_mom = Column(Float, nullable=True, comment="原材料环比(%)")
    ppi_living_mom = Column(Float, nullable=True, comment="生活资料环比(%)")
    ppi_cg_mom = Column(Float, nullable=True, comment="消费品环比(%)")
    raw_json = Column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawCnPpi({self.month})>"


class RawSfMonth(TimestampMixin, Base):
    """社会融资规模 (sf_month).

    Tushare pro.sf_month(start_period=..., end_period=...).
    """
    __tablename__ = "raw_sf_month"
    __table_args__ = (
        {"comment": "社会融资规模月度数据"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(String(8), nullable=False, index=True, unique=True, comment="月份")
    afre = Column(Float, nullable=True, comment="社融增量(亿元)")
    t_afre = Column(Float, nullable=True, comment="社融增量累计(亿元)")
    t_m_afre = Column(Float, nullable=True, comment="社融增量累计同比(%)")
    rmb_loan = Column(Float, nullable=True, comment="人民币贷款(亿元)")
    fx_loan = Column(Float, nullable=True, comment="外币贷款(亿元)")
    entrust_loan = Column(Float, nullable=True, comment="委托贷款(亿元)")
    trust_loan = Column(Float, nullable=True, comment="信托贷款(亿元)")
    undisc_bill = Column(Float, nullable=True, comment="未贴现银行承兑汇票(亿元)")
    corp_bond = Column(Float, nullable=True, comment="企业债券(亿元)")
    gov_bond = Column(Float, nullable=True, comment="政府债券(亿元)")
    abs = Column(Float, nullable=True, comment="资产支持证券(亿元)")
    net_fin = Column(Float, nullable=True, comment="非金融企业境内股票融资(亿元)")
    n_stock = Column(Float, nullable=True, comment="股票融资(亿元)")
    external_loan = Column(Float, nullable=True, comment="外部贷款(亿元)")
    raw_json = Column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawSfMonth({self.month})>"


class RawYieldCurve(TimestampMixin, Base):
    """国债收益率曲线 (yield_curve).

    Source: Tushare yield_curve API
    Fields: ts_code, trade_date, curve_type, curve_term, yield_value
    ts_code examples: 'CGB1Y', 'CGB5Y', 'CGB10Y'
    Note: May require specific Tushare permissions/version.
    """
    __tablename__ = "raw_yield_curve"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_raw_yield_curve_code_date"),
        {"comment": "国债收益率曲线 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(16), nullable=False, index=True, comment="曲线代码")
    trade_date = Column(String(8), nullable=False, index=True, comment="交易日期")
    curve_type = Column(String(32), nullable=True, comment="曲线类型")
    curve_term = Column(Float, nullable=True, comment="期限(年)")
    yield_value = Column(Float, nullable=True, comment="收益率(%)")
    raw_json = Column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawYieldCurve({self.ts_code}, {self.trade_date})>"
