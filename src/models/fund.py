"""Fund / ETF data — ETF日线、持仓."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger
from src.models.base import TimestampMixin, Base


class RawFundDaily(TimestampMixin, Base):
    """ETF/LOF基金日线行情 (fund_daily)."""
    __tablename__ = "raw_fund_daily"

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


class RawFundPortfolio(TimestampMixin, Base):
    """基金持仓 (fund_portfolio)."""
    __tablename__ = "raw_fund_portfolio"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    end_date = Column(String(8), nullable=False)
    symbol = Column(String(16))
    mkv = Column(Float)            # 持有股票市值（万元）
    amount = Column(Float)
    stk_mkv_ratio = Column(Float)  # 占股票投资市值比


class RawFundBasic(TimestampMixin, Base):
    """基金基本信息 (fund_basic).

    Source: Tushare fund_basic API
    Fields: ts_code, name, management, custodian, fund_type, found_date,
            issue_date, issue_amount, invest_type, type, trustee,
            purc_startdate, red_startdate, m_fee, c_fee, benchmark, status
    """
    __tablename__ = "raw_fund_basic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True, unique=True)
    name = Column(String(128), nullable=True)
    management = Column(String(128), nullable=True)   # 管理人
    custodian = Column(String(128), nullable=True)    # 托管人
    fund_type = Column(String(32), nullable=True)     # 基金类型
    found_date = Column(String(8), nullable=True)     # 成立日期
    issue_date = Column(String(8), nullable=True)     # 发行日期
    issue_amount = Column(Float, nullable=True)       # 发行份额(亿)
    invest_type = Column(String(32), nullable=True)   # 投资类型
    type = Column(String(32), nullable=True)           # 类型
    trustee = Column(String(128), nullable=True)       # 受托人
    purc_startdate = Column(String(8), nullable=True) # 申购起始日
    red_startdate = Column(String(8), nullable=True)  # 赎回起始日
    m_fee = Column(Float, nullable=True)              # 管理费率(%)
    c_fee = Column(Float, nullable=True)              # 托管费率(%)
    benchmark = Column(String(256), nullable=True)     # 业绩基准
    status = Column(String(8), nullable=True)          # 状态


class RawFundNav(TimestampMixin, Base):
    """基金净值 (fund_nav).

    Source: Tushare fund_nav API
    Fields: ts_code, ann_date, nav_date, unit_nav, accum_nav, adj_nav
    """
    __tablename__ = "raw_fund_nav"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    ann_date = Column(String(8), nullable=True)       # 公告日期
    nav_date = Column(String(8), nullable=False, index=True)  # 净值日期
    unit_nav = Column(Float, nullable=True)           # 单位净值
    accum_nav = Column(Float, nullable=True)          # 累计净值
    adj_nav = Column(Float, nullable=True)            # 复权净值
