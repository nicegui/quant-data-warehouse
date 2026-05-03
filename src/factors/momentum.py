"""动量/反转因子."""

from __future__ import annotations
import numpy as np
import pandas as pd
from src.factors.data import read_stock_daily
from src.factors.utils import process_factor


def _calc_ret(close: pd.DataFrame, period: int, skip: int = 1) -> pd.DataFrame:
    """计算过去 N 日收益率 (跳过最近 skip 天)."""
    return close.pct_change(period).shift(skip)


def ret_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """过去1月收益率 (跳过最近1天)."""
    close = read_stock_daily(start_date, end_date)
    df = _calc_ret(close, 21, skip=1)
    return process_factor(df)


def ret_3m(start_date=None, end_date=None) -> pd.DataFrame:
    """过去3月收益率."""
    close = read_stock_daily(start_date, end_date)
    df = _calc_ret(close, 63, skip=1)
    return process_factor(df)


def ret_6m(start_date=None, end_date=None) -> pd.DataFrame:
    """过去6月收益率."""
    close = read_stock_daily(start_date, end_date)
    df = _calc_ret(close, 126, skip=1)
    return process_factor(df)


def ret_12m_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """经典12-1月动量. 过去12个月(跳过最近1月)的收益率."""
    close = read_stock_daily(start_date, end_date)
    ret_12m = _calc_ret(close, 252, skip=1)
    ret_1m_raw = _calc_ret(close, 21, skip=1)
    df = (1 + ret_12m) / (1 + ret_1m_raw) - 1  # 去最近1月
    return process_factor(df)


def ret_1m_reverse(start_date=None, end_date=None) -> pd.DataFrame:
    """短期反转 (含最近1天, 取负号 → 反转)."""
    close = read_stock_daily(start_date, end_date)
    df = _calc_ret(close, 21, skip=0)
    return process_factor(-df)


def max_ret_1m(start_date=None, end_date=None) -> pd.DataFrame:
    """月内最大日收益."""
    close = read_stock_daily(start_date, end_date)
    daily_ret = close.pct_change()
    df = daily_ret.rolling(21, min_periods=10).max()
    return process_factor(df)
