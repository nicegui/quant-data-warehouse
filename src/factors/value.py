"""价值/估值因子."""

from __future__ import annotations
import pandas as pd
from src.factors.data import read_daily_basic
from src.factors.utils import process_factor


def pe_ttm(start_date=None, end_date=None) -> pd.DataFrame:
    """市盈率 (TTM). 值越低越便宜."""
    data = read_daily_basic(start_date, end_date, fields=["pe_ttm"])
    df = data["pe_ttm"].copy()
    df[df <= 0] = None  # 负PE无意义
    return process_factor(1.0 / df)  # 取倒数: 盈利收益率, 越大越好


def pb_lf(start_date=None, end_date=None) -> pd.DataFrame:
    """市净率 (最新财报). 值越低越便宜."""
    data = read_daily_basic(start_date, end_date, fields=["pb"])
    df = data["pb"].copy()
    df[df <= 0] = None
    return process_factor(1.0 / df)  # BM比


def ep_ttm(start_date=None, end_date=None) -> pd.DataFrame:
    """盈利收益率 = 1/PE_TTM."""
    return pe_ttm(start_date, end_date)  # 已实现


def sp_ttm(start_date=None, end_date=None) -> pd.DataFrame:
    """市销率倒数."""
    data = read_daily_basic(start_date, end_date, fields=["ps_ttm"])
    df = data["ps_ttm"].copy()
    df[df <= 0] = None
    return process_factor(1.0 / df)


def div_yield(start_date=None, end_date=None) -> pd.DataFrame:
    """股息率."""
    data = read_daily_basic(start_date, end_date, fields=["dv_ttm"])
    df = data["dv_ttm"].copy()
    df[df <= 0] = None
    return process_factor(df)
