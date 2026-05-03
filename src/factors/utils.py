"""因子工具函数 — 标准化/去极值/中性化."""

from __future__ import annotations
import numpy as np
import pandas as pd


def winsorize(series: pd.Series, pct: float = 0.01) -> pd.Series:
    """去极值: 将超出[pct, 1-pct]分位的值截断."""
    lo, hi = series.quantile(pct), series.quantile(1 - pct)
    return series.clip(lo, hi)


def standardize(series: pd.Series) -> pd.Series:
    """Z-score 标准化 (减去均值除以标准差)."""
    mean, std = series.mean(), series.std()
    if std == 0 or pd.isna(std):
        return pd.Series(0, index=series.index)
    return (series - mean) / std


def process_factor(factor_df: pd.DataFrame, winsorize_pct: float = 0.01) -> pd.DataFrame:
    """对因子 DataFrame (date × ts_code) 执行截面标准化流程.
    
    每期 (每行) 独立处理: 去极值 → Z-score.
    """
    result = factor_df.copy()
    for idx in result.index:
        row = result.loc[idx]
        row = winsorize(row, winsorize_pct)
        result.loc[idx] = standardize(row)
    return result


def neutralise(factor_df: pd.DataFrame, industry_df: pd.DataFrame, 
               mktcap_df: pd.DataFrame) -> pd.DataFrame:
    """行业+市值中性化: 因子值对行业哑变量+对数市值做截面回归取残差.
    
    Args:
        factor_df: date × ts_code 因子值
        industry_df: date × ts_code 申万行业代码 (或可对齐)
        mktcap_df: date × ts_code 对数市值
    
    Returns:
        残差因子 DataFrame
    """
    result = factor_df.copy()
    common_dates = factor_df.index.intersection(mktcap_df.index)
    
    for date in common_dates:
        fv = factor_df.loc[date].dropna()
        mv = mktcap_df.loc[date].dropna()
        ind = industry_df.loc[date].dropna() if date in industry_df.index else None
        
        common_stocks = fv.index.intersection(mv.index)
        if ind is not None:
            common_stocks = common_stocks.intersection(ind.index)
        if len(common_stocks) < 30:
            continue
        
        X = pd.DataFrame({"mktcap": mv.loc[common_stocks]})
        if ind is not None:
            ind_dummies = pd.get_dummies(ind.loc[common_stocks], drop_first=True)
            X = pd.concat([X, ind_dummies], axis=1)
        
        y = fv.loc[common_stocks]
        X = X.dropna()
        y = y.loc[X.index]
        
        try:
            from numpy.linalg import lstsq
            beta, _, _, _ = lstsq(X.values, y.values)
            pred = X.values @ beta
            residual = y.values - pred
            result.loc[date, X.index] = residual
        except Exception:
            pass
    
    return result


def save_factor(df: pd.DataFrame, name: str, data_dir: str = "data/factors"):
    """保存因子到 parquet."""
    import os
    os.makedirs(data_dir, exist_ok=True)
    stacked = df.stack().reset_index()
    stacked.columns = ["trade_date", "ts_code", "value"]
    stacked.to_parquet(f"{data_dir}/{name}.parquet", index=False)
    return stacked


def make_index_map(dates: pd.DatetimeIndex, stocks: pd.Index) -> pd.DataFrame:
    """创建空的 factor DataFrame 框架."""
    return pd.DataFrame(index=dates, columns=stocks, dtype=float)
