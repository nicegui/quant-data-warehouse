"""宏观/市场状态因子."""

from __future__ import annotations
import numpy as np
import pandas as pd
from src.factors.data import read_index_daily, read_daily_basic, read_macro_indicator
from src.factors.utils import process_factor


def market_pe_pct(start_date=None, end_date=None) -> pd.DataFrame:
    """沪深300 PE 历史分位. 返回的时间序列截面为全市场统一值."""
    # 用 raw_index_dailybasic 获取 沪深300 PE
    from src.db.engine import get_session
    s = get_session()
    sql = """
        SELECT trade_date::date AS trade_date, pe_ttm
        FROM raw_index_dailybasic
        WHERE ts_code = '000300.SH' AND pe_ttm IS NOT NULL
        ORDER BY trade_date
    """
    df = pd.read_sql(sql, s.bind)
    s.close()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date")
    
    if df.empty:
        return pd.DataFrame()
    
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]
    
    # 滚动5年分位
    result = pd.DataFrame(index=df.index, columns=["MARKET"], dtype=float)
    for i, date in enumerate(df.index):
        window = df.iloc[max(0, i-1260):i+1]["pe_ttm"]
        if len(window) < 252:
            continue
        result.loc[date, "MARKET"] = (df.loc[date, "pe_ttm"] <= window).mean()
    
    return process_factor(result)


def cn_us_spread_10y(start_date=None, end_date=None) -> pd.DataFrame:
    """中美10年期利差."""
    df = read_macro_indicator(["cn_bond_10y", "us_bond_10y"])
    if df.empty:
        return pd.DataFrame()
    
    cn = df[df["source"] == "cn_bond_10y"].pivot(index="date", columns="sub_key", values="value")
    us = df[df["source"] == "us_bond_10y"].pivot(index="date", columns="sub_key", values="value")
    
    # Both should have single column 'value'
    cn_val = cn["value"] if "value" in cn.columns else cn.iloc[:, 0]
    us_val = us["value"] if "value" in us.columns else us.iloc[:, 0]
    
    common = cn_val.index.intersection(us_val.index)
    spread = pd.DataFrame(index=common, columns=["MARKET"], dtype=float)
    spread["MARKET"] = cn_val.loc[common].values - us_val.loc[common].values
    
    if start_date:
        spread = spread[spread.index >= start_date]
    if end_date:
        spread = spread[spread.index <= end_date]
    
    return process_factor(spread)


def bdi_momentum(start_date=None, end_date=None) -> pd.DataFrame:
    """BDI 3月动量."""
    from src.db.engine import get_session
    s = get_session()
    sql = """
        SELECT date::date AS date, value
        FROM raw_commodity_logistics
        WHERE source = 'freight' AND sub_index LIKE '%BDI'
        ORDER BY date
    """
    df = pd.read_sql(sql, s.bind, index_col="date")
    s.close()
    
    if df.empty:
        return pd.DataFrame()
    
    df["ret_3m"] = df["value"].pct_change(63)
    result = pd.DataFrame(index=df.index, columns=["MARKET"], dtype=float)
    result["MARKET"] = df["ret_3m"]
    
    if start_date:
        result = result[result.index >= start_date]
    if end_date:
        result = result[result.index <= end_date]
    
    return process_factor(result)


def qvix_level(start_date=None, end_date=None) -> pd.DataFrame:
    """QVIX 恐慌指数."""
    from src.db.engine import get_session
    s = get_session()
    sql = """
        SELECT trade_date::date AS date, close AS value
        FROM raw_qvix
        WHERE underlying = '50ETF' AND close IS NOT NULL
        ORDER BY date
    """
    df = pd.read_sql(sql, s.bind, index_col="date")
    s.close()
    
    if df.empty:
        return pd.DataFrame()
    
    result = pd.DataFrame(index=df.index, columns=["MARKET"], dtype=float)
    result["MARKET"] = df["value"]
    
    if start_date:
        result = result[result.index >= start_date]
    if end_date:
        result = result[result.index <= end_date]
    
    return process_factor(result)


def margin_balance_ratio(start_date=None, end_date=None) -> pd.DataFrame:
    """融资余额变化率 (月度)."""
    from src.db.engine import get_session
    s = get_session()
    sql = """
        SELECT trade_date::date AS date, rzye AS balance
        FROM raw_margin_total
        WHERE rzye IS NOT NULL
        ORDER BY date
    """
    df = pd.read_sql(sql, s.bind, index_col="date")
    s.close()
    
    if df.empty:
        return pd.DataFrame()
    
    df["change"] = df["balance"].pct_change(21)
    result = pd.DataFrame(index=df.index, columns=["MARKET"], dtype=float)
    result["MARKET"] = df["change"]
    
    if start_date:
        result = result[result.index >= start_date]
    if end_date:
        result = result[result.index <= end_date]
    
    return process_factor(result)
