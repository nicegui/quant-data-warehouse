"""Pydantic schemas for data validation and transformation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RawStockDailySchema(BaseModel):
    """Schema for raw A-share daily data from Tushare API."""
    ts_code: str
    trade_date: datetime
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_chg: float
    vol: float
    amount: float


class CuratedStockDailyAdjSchema(BaseModel):
    """Schema for forward-adjusted (前复权) daily data."""
    asset_id: str  # UUID string
    trade_date: datetime
    open_adj: float
    high_adj: float
    low_adj: float
    close_adj: float
    volume: float
    amount: float
    adj_factor: float


class ConsultationSchema(BaseModel):
    """Schema for Tushare news consultation."""
    news_id: str
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    pub_time: datetime


class FinancialReportSchema(BaseModel):
    """Schema for financial report data."""
    ts_code: str
    end_date: datetime
    revenue: Optional[float] = None
    operating_profit: Optional[float] = None
    net_profit: Optional[float] = None


class FinancialIndicatorSchema(BaseModel):
    """Schema for financial indicators."""
    ts_code: str
    end_date: datetime
    eps: Optional[float] = None
    roe: Optional[float] = None
    bps: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None


class StockBasicSchema(BaseModel):
    """Schema for stock master data."""
    ts_code: str
    symbol: str
    name: str
    area: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None
    list_date: Optional[datetime] = None
    delist_date: Optional[datetime] = None
    is_hs: Optional[str] = None


class AdjFactorSchema(BaseModel):
    """Schema for forward adjustment factor."""
    ts_code: str
    trade_date: datetime
    adj_factor: float


class CryptoOhlcvSchema(BaseModel):
    """Schema for crypto OHLCV data (Phase 2)."""
    exchange: str
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str
