"""Money flow / 资金流向 — 个股资金流、沪深港通、融资融券."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger
from src.models.base import TimestampMixin, Base


class RawMoneyflow(TimestampMixin, Base):
    """个股资金流 (moneyflow) — 逐日."""
    __tablename__ = "raw_moneyflow"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    buy_sm_vol = Column(Float)      # 小单买入量（手）
    buy_sm_amount = Column(Float)   # 小单买入金额（万元）
    sell_sm_vol = Column(Float)
    sell_sm_amount = Column(Float)
    buy_md_vol = Column(Float)      # 中单
    buy_md_amount = Column(Float)
    sell_md_vol = Column(Float)
    sell_md_amount = Column(Float)
    buy_lg_vol = Column(Float)      # 大单
    buy_lg_amount = Column(Float)
    sell_lg_vol = Column(Float)
    sell_lg_amount = Column(Float)
    buy_elg_vol = Column(Float)     # 特大单
    buy_elg_amount = Column(Float)
    sell_elg_vol = Column(Float)
    sell_elg_amount = Column(Float)
    net_mf_vol = Column(Float)      # 净流入量（手）
    net_mf_amount = Column(Float)   # 净流入额（万元）

    def __repr__(self):
        return f"<RawMoneyflow({self.ts_code}, {self.trade_date})>"


class RawMoneyflowMktDc(TimestampMixin, Base):
    """大盘资金流 (moneyflow_mkt_dc)."""
    __tablename__ = "raw_moneyflow_mkt_dc"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, unique=True)
    s_d_value = Column(Float)       # 小单净流入
    m_d_value = Column(Float)       # 中单
    l_d_value = Column(Float)       # 大单
    el_d_value = Column(Float)      # 特大单
    net_main = Column(Float)        # 主力净流入
    net_main_pct = Column(Float)    # 主力净占比


class RawHsgtTop10(TimestampMixin, Base):
    """沪深港通十大成交 (hsgt_top10)."""
    __tablename__ = "raw_hsgt_top10"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False)
    name = Column(String(64))
    close = Column(Float)
    pct_change = Column(Float)
    rank = Column(String(8))        # 1：沪股通 2：深股通
    buy_amount = Column(Float)      # 买入金额（亿元）
    sell_amount = Column(Float)     # 卖出金额（亿元）
    net_amount = Column(Float)      # 净买入金额（亿元）


class RawGgtTop10(TimestampMixin, Base):
    """港股通十大成交 (ggt_top10)."""
    __tablename__ = "raw_ggt_top10"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False)
    name = Column(String(64))
    close = Column(Float)
    pct_change = Column(Float)
    rank = Column(String(8))
    buy_amount = Column(Float)
    sell_amount = Column(Float)
    net_amount = Column(Float)


class RawMarginDetail(TimestampMixin, Base):
    """融资融券明细 (margin_detail)."""
    __tablename__ = "raw_margin_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64))
    rzye = Column(Float)            # 融资余额（元）
    rzmre = Column(Float)           # 融资买入额（元）
    rzche = Column(Float)           # 融资偿还额（元）
    rqye = Column(Float)            # 融券余额（元）
    rqmcl = Column(Float)           # 融券卖出量（股）
    rzrqye = Column(Float)          # 融资融券余额（元）


class RawMarginTotal(TimestampMixin, Base):
    """融资融券总量 (margin) — 大盘汇总，非个股明细.

    Source: Tushare margin API (not margin_detail)
    Fields: trade_date, rzye, rzmre, rzche, rqye, rqmcl, rzrqye
    """
    __tablename__ = "raw_margin_total"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, unique=True)
    rzye = Column(Float)            # 融资余额（元）
    rzmre = Column(Float)           # 融资买入额（元）
    rzche = Column(Float)           # 融资偿还额（元）
    rqye = Column(Float)            # 融券余额（元）
    rqmcl = Column(Float)           # 融券卖出量（股）
    rzrqye = Column(Float)          # 融资融券余额（元）
