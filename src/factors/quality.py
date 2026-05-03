"""质量/盈利因子."""

from __future__ import annotations
import numpy as np
import pandas as pd
from src.factors.data import read_financial_indicators, read_daily_basic, read_stock_daily
from src.factors.utils import process_factor


def roe_ttm(start_date=None, end_date=None) -> pd.DataFrame:
    """ROE (TTM)."""
    df = read_financial_indicators(start_date, end_date, fields=["roe"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="roe")
    pivot = pivot.ffill(limit=4)  # 季度数据填充
    return process_factor(pivot)


def roa_ttm(start_date=None, end_date=None) -> pd.DataFrame:
    """ROA (TTM)."""
    df = read_financial_indicators(start_date, end_date, fields=["roa"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="roa")
    pivot = pivot.ffill(limit=4)
    return process_factor(pivot)


def gross_margin(start_date=None, end_date=None) -> pd.DataFrame:
    """毛利率."""
    df = read_financial_indicators(start_date, end_date, fields=["grossprofit_margin"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="grossprofit_margin")
    pivot = pivot.ffill(limit=4)
    return process_factor(pivot)


def net_margin(start_date=None, end_date=None) -> pd.DataFrame:
    """净利率."""
    df = read_financial_indicators(start_date, end_date, fields=["netprofit_margin"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="netprofit_margin")
    pivot = pivot.ffill(limit=4)
    return process_factor(pivot)


def debt_to_assets(start_date=None, end_date=None) -> pd.DataFrame:
    """资产负债率 (越低越好, 取负号)."""
    df = read_financial_indicators(start_date, end_date, fields=["debt_to_assets"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="debt_to_assets")
    pivot = pivot.ffill(limit=4)
    return process_factor(-pivot)


def earnings_stability(start_date=None, end_date=None) -> pd.DataFrame:
    """盈利稳定性 — 5年 EPS 变异系数，越低越稳定(取负号)."""
    df = read_financial_indicators(start_date, end_date, fields=["profit_dedt", "roe"])
    pivot = df.pivot_table(
        index="trade_date", columns="ts_code", values="profit_dedt", aggfunc="last"
    )
    pivot = pivot.ffill(limit=20)
    rolling_std = pivot.rolling(20, min_periods=8).std()
    rolling_mean = pivot.rolling(20, min_periods=8).mean()
    cv = rolling_std / rolling_mean.abs()
    cv.replace([np.inf, -np.inf], np.nan, inplace=True)
    return process_factor(-cv)
