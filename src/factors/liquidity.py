"""流动性/规模因子."""

from __future__ import annotations
import numpy as np
import pandas as pd
from src.factors.data import read_daily_basic, read_stock_daily
from src.factors.utils import process_factor


def ln_market_cap(start_date=None, end_date=None) -> pd.DataFrame:
    """对数总市值."""
    data = read_daily_basic(start_date, end_date, fields=["total_mv"])
    df = data["total_mv"].copy()
    df[df <= 0] = None
    return process_factor(np.log(df))


def turnover_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """月均换手率."""
    data = read_daily_basic(start_date, end_date, fields=["turnover_rate"])
    df = data["turnover_rate"].copy()
    # turnover_rate 已是百分比, 直接 rolling mean
    result = df.rolling(21, min_periods=10).mean()
    return process_factor(result)


def turnover_cv(start_date=None, end_date=None) -> pd.DataFrame:
    """换手率变异系数 (标准差/均值) — 筹码不稳定度."""
    data = read_daily_basic(start_date, end_date, fields=["turnover_rate"])
    df = data["turnover_rate"].copy()
    mean_t = df.rolling(21, min_periods=10).mean()
    std_t = df.rolling(21, min_periods=10).std()
    result = std_t / mean_t
    result.replace([np.inf, -np.inf], np.nan, inplace=True)
    return process_factor(result)


def amihud_illiq(start_date=None, end_date=None) -> pd.DataFrame:
    """Amihud 非流动性: |ret| / dollar_volume."""
    close = read_stock_daily(start_date, end_date)
    ret = close.pct_change().abs()
    
    data = read_daily_basic(start_date, end_date, fields=["total_mv", "turnover_rate"])
    # dollar_volume ≈ total_mv * turnover_rate / 100 (万元)
    dollar_vol = data["total_mv"] * data["turnover_rate"] / 100
    
    # Align
    common_dates = ret.index.intersection(dollar_vol.index)
    common_stocks = ret.columns.intersection(dollar_vol.columns)
    ret = ret.loc[common_dates, common_stocks]
    dollar_vol = dollar_vol.loc[common_dates, common_stocks]
    
    illiq = (ret / dollar_vol.clip(lower=1e-8)).rolling(21, min_periods=10).mean()
    return process_factor(illiq)


def dollar_volume_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """月均成交额 (取对数)."""
    data = read_daily_basic(start_date, end_date, fields=["total_mv", "turnover_rate"])
    dollar_vol = data["total_mv"] * data["turnover_rate"] / 100
    result = np.log(dollar_vol.rolling(21, min_periods=10).mean().clip(lower=1))
    return process_factor(result)
