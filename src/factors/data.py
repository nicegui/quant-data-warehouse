"""因子数据读取层."""

from __future__ import annotations
import numpy as np
import pandas as pd
from sqlalchemy import text
from src.db.engine import get_engine


def _query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """通用查询."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    except Exception:
        return pd.DataFrame()


def _add_date_filters(params: dict, conditions: list, start_date=None, end_date=None,
                      date_col: str = "trade_date"):
    """Helper: add date range filters."""
    if start_date:
        conditions.append(f"{date_col} >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append(f"{date_col} <= :end_date")
        params["end_date"] = end_date


# ── 行情 ──

def read_stock_daily(start_date=None, end_date=None) -> pd.DataFrame:
    conditions = ["close IS NOT NULL"]
    params = {}
    _add_date_filters(params, conditions, start_date, end_date)
    sql = f"""
        SELECT ts_code, trade_date::date AS trade_date, close
        FROM raw_stock_daily WHERE {' AND '.join(conditions)} ORDER BY trade_date
    """
    df = _query(sql, params)
    if df.empty: return pd.DataFrame()
    return df.pivot(index="trade_date", columns="ts_code", values="close")


def read_ohlcv(start_date=None, end_date=None) -> dict[str, pd.DataFrame]:
    """读取全量 OHLCV 价量数据，返回各字段的 pivot DataFrame.
    
    Returns:
        {'open': DataFrame, 'high': ..., 'low': ..., 'close': ..., 
         'volume': ..., 'amount': ..., 'vwap': ...}
    每张 DataFrame 形状: date × ts_code
    """
    conditions = ["close IS NOT NULL", "open IS NOT NULL", "high IS NOT NULL", 
                   "low IS NOT NULL", "vol IS NOT NULL"]
    params = {}
    _add_date_filters(params, conditions, start_date, end_date)
    sql = f"""
        SELECT ts_code, trade_date::date AS trade_date, 
               open, high, low, close, 
               vol AS volume, amount
        FROM raw_stock_daily WHERE {' AND '.join(conditions)} ORDER BY trade_date
    """
    df = _query(sql, params)
    if df.empty:
        return {k: pd.DataFrame() for k in ['open','high','low','close','volume','amount','vwap']}
    
    result = {}
    for field in ['open', 'high', 'low', 'close', 'volume', 'amount']:
        result[field] = df.pivot(index="trade_date", columns="ts_code", values=field)
    
    # 用 amount/volume 近似 vwap
    piv_amount = df.pivot(index="trade_date", columns="ts_code", values="amount")
    piv_volume = df.pivot(index="trade_date", columns="ts_code", values="volume")
    result['vwap'] = (piv_amount / piv_volume.replace(0, np.nan)).fillna(result['close'])
    
    return result


def read_index_daily(index_code="000300.SH", start_date=None, end_date=None) -> pd.DataFrame:
    conditions = ["ts_code = :code"]
    params = {"code": index_code}
    _add_date_filters(params, conditions, start_date, end_date)
    sql = f"""
        SELECT trade_date::date AS trade_date, close
        FROM raw_index_daily WHERE {' AND '.join(conditions)} ORDER BY trade_date
    """
    df = _query(sql, params)
    if df.empty: return pd.DataFrame()
    return df.set_index("trade_date")


# ── 基本面 ──

def read_daily_basic(start_date=None, end_date=None, fields=None) -> dict:
    if fields is None:
        fields = ["pe_ttm", "pb", "total_mv", "turnover_rate"]
    conditions = []
    params = {}
    _add_date_filters(params, conditions, start_date, end_date)
    cols = ", ".join(fields)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT ts_code, trade_date::date AS trade_date, {cols} FROM raw_daily_basic {where} ORDER BY trade_date"
    df = _query(sql, params)
    if df.empty: return {f: pd.DataFrame() for f in fields}
    result = {}
    for f in fields:
        result[f] = df.pivot(index="trade_date", columns="ts_code", values=f) if f in df.columns else pd.DataFrame()
    return result


def read_financial_indicators(start_date=None, end_date=None, fields=None) -> pd.DataFrame:
    if fields is None:
        fields = ["roe", "roa", "grossprofit_margin", "netprofit_margin",
                  "debt_to_assets", "or_yoy", "profit_dedt"]
    conditions = []
    params = {}
    _add_date_filters(params, conditions, start_date, end_date, date_col="end_date")
    cols = ", ".join(fields)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT ts_code, end_date::date AS trade_date, {cols} FROM raw_financial_indicators {where} ORDER BY end_date"
    return _query(sql, params)


# ── 另类/情绪 ──

def read_macro_indicator(sources: list[str]) -> pd.DataFrame:
    placeholders = ",".join(f":s{i}" for i in range(len(sources)))
    params = {f"s{i}": s for i, s in enumerate(sources)}
    sql = f"""
        SELECT date::date AS date, sub_key, value, source
        FROM raw_macro_indicator WHERE source IN ({placeholders}) AND value IS NOT NULL ORDER BY date
    """
    return _query(sql, params)


def read_peer_comparison(dimension="valuation") -> pd.DataFrame:
    return _query("""
        SELECT target_symbol AS ts_code, code AS peer_code, dimension, rank_info, raw_json
        FROM raw_peer_comparison WHERE dimension = :dim
    """, {"dim": dimension})


def read_moneyflow(start_date=None, end_date=None) -> pd.DataFrame:
    conditions = []
    params = {}
    _add_date_filters(params, conditions, start_date, end_date)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT ts_code, trade_date::date AS trade_date,
               net_mf_vol, net_mf_amount
        FROM raw_moneyflow {where} ORDER BY trade_date
    """
    return _query(sql, params)
