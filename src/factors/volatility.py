"""波动/风险因子."""

from __future__ import annotations
import numpy as np
import pandas as pd
from src.factors.data import read_stock_daily, read_index_daily
from src.factors.utils import process_factor


def vol_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """21日年化波动率."""
    close = read_stock_daily(start_date, end_date)
    daily_ret = close.pct_change()
    df = daily_ret.rolling(21, min_periods=10).std() * np.sqrt(252)
    return process_factor(df)


def vol_3m(start_date=None, end_date=None) -> pd.DataFrame:
    """63日年化波动率."""
    close = read_stock_daily(start_date, end_date)
    daily_ret = close.pct_change()
    df = daily_ret.rolling(63, min_periods=30).std() * np.sqrt(252)
    return process_factor(df)


def downside_vol_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """下行波动率 (只计负收益)."""
    close = read_stock_daily(start_date, end_date)
    daily_ret = close.pct_change()
    down = daily_ret.copy()
    down[down > 0] = 0
    df = down.rolling(21, min_periods=10).std() * np.sqrt(252)
    return process_factor(df)


def skew_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """日收益偏度."""
    close = read_stock_daily(start_date, end_date)
    daily_ret = close.pct_change()
    df = daily_ret.rolling(21, min_periods=10).skew()
    return process_factor(df)


def beta_1y(start_date=None, end_date=None) -> pd.DataFrame:
    """1年 Beta (对沪深300)."""
    close = read_stock_daily(start_date, end_date)
    index_close = read_index_daily("000300.SH", start_date, end_date)
    
    stock_ret = close.pct_change()
    index_ret = index_close["close"].pct_change()
    
    # Rolling beta: cov(stock, market) / var(market)
    result = pd.DataFrame(index=stock_ret.index, columns=stock_ret.columns, dtype=float)
    
    for code in stock_ret.columns:
        s = stock_ret[code]
        common = s.dropna().index.intersection(index_ret.dropna().index)
        if len(common) < 60:
            continue
        s_aligned = s.loc[common]
        m_aligned = index_ret.loc[common]
        
        cov = s_aligned.rolling(252, min_periods=60).cov(m_aligned)
        var = m_aligned.rolling(252, min_periods=60).var()
        beta = cov / var
        result[code] = beta
    
    return process_factor(result)


def idiosyncratic_vol(start_date=None, end_date=None) -> pd.DataFrame:
    """特质波动率 (CAPM 残差)."""
    close = read_stock_daily(start_date, end_date)
    index_close = read_index_daily("000300.SH", start_date, end_date)
    
    stock_ret = close.pct_change()
    index_ret = index_close["close"].pct_change()
    
    result = pd.DataFrame(index=stock_ret.index, columns=stock_ret.columns, dtype=float)
    
    for code in stock_ret.columns:
        s = stock_ret[code]
        common = s.dropna().index.intersection(index_ret.dropna().index)
        if len(common) < 60:
            continue
        s_aligned = s.loc[common]
        m_aligned = index_ret.loc[common]
        
        # Rolling regression: residual std
        for i in range(60, len(common)):
            s_win = s_aligned.iloc[i-60:i]
            m_win = m_aligned.iloc[i-60:i]
            if m_win.std() == 0:
                continue
            beta = np.cov(s_win, m_win)[0, 1] / m_win.var()
            alpha = s_win.mean() - beta * m_win.mean()
            resid = s_win - (alpha + beta * m_win)
            result.loc[common[i], code] = resid.std() * np.sqrt(252)
    
    return process_factor(result)
