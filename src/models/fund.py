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
