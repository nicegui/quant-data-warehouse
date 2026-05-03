"""成长性因子."""

from __future__ import annotations
import pandas as pd
from src.factors.data import read_financial_indicators
from src.factors.utils import process_factor


def revenue_growth_yoy(start_date=None, end_date=None) -> pd.DataFrame:
    """营收同比增长率."""
    df = read_financial_indicators(start_date, end_date, fields=["or_yoy"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="or_yoy")
    pivot = pivot.ffill(limit=4)
    return process_factor(pivot)


def earnings_growth_yoy(start_date=None, end_date=None) -> pd.DataFrame:
    """净利润同比增长率."""
    df = read_financial_indicators(start_date, end_date, fields=["profit_dedt"])
    pivot = df.pivot(index="trade_date", columns="ts_code", values="profit_dedt")
    pivot = pivot.ffill(limit=4)
    return process_factor(pivot)


def asset_growth_yoy(start_date=None, end_date=None) -> pd.DataFrame:
    """总资产同比增长率 (需从资产负债表推算, 暂用 finanial_indicator 代理)."""
    return revenue_growth_yoy(start_date, end_date)  # FIXME: 用真实资产增长率
