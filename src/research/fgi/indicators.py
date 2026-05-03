"""Fear & Greed Index — 8 indicators for A-share market sentiment.

Scoring method (per indicator):
  1. Compute raw value for each trading day
  2. Rolling 252-day percentile rank → 0-100 score
  3. For inverse indicators (volatility), invert: score = 100 - percentile
  4. Final FGI = equal-weight average of all 8 scores
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.db.session import db_session

logger = logging.getLogger(__name__)


def _rolling_pct_rank(series: pd.Series, window: int = 252) -> pd.Series:
    """Rolling percentile rank within window. Returns 0-100."""
    return series.rolling(window, min_periods=60).rank(pct=True) * 100


def _rolling_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """Rolling Z-score."""
    rmean = series.rolling(window, min_periods=20).mean()
    rstd = series.rolling(window, min_periods=20).std()
    return (series - rmean) / rstd.replace(0, np.nan)


# ── Indicator 1: Price Momentum ──

def compute_price_momentum() -> pd.DataFrame:
    """沪深300 收盘价 vs 250日均线偏离百分比."""
    sql = """
        SELECT trade_date, close
        FROM raw_index_daily
        WHERE ts_code = '000300.SH'
        ORDER BY trade_date
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date").sort_index()
    df["ma250"] = df["close"].rolling(250, min_periods=60).mean()
    df["momentum"] = (df["close"] - df["ma250"]) / df["ma250"] * 100  # % deviation
    return df[["momentum"]]


# ── Indicator 2: Market Breadth ──

def compute_market_breadth() -> pd.DataFrame:
    """全指数中收盘价在 20 日均线上方的占比."""
    sql = """
        SELECT trade_date, ts_code, close
        FROM raw_index_daily
        ORDER BY trade_date, ts_code
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values(["ts_code", "trade_date"])
    df["ma20"] = df.groupby("ts_code")["close"].transform(
        lambda x: x.rolling(20, min_periods=5).mean()
    )
    df["above_ma"] = (df["close"] > df["ma20"]).astype(int)
    daily = df.groupby("trade_date").agg(
        total=("ts_code", "count"),
        above=("above_ma", "sum"),
    )
    daily["breadth"] = daily["above"] / daily["total"] * 100
    return daily[["breadth"]]


# ── Indicator 3: Volatility ──

def compute_volatility() -> pd.DataFrame:
    """沪深300 30日年化波动率."""
    sql = """
        SELECT trade_date, pct_chg
        FROM raw_index_daily
        WHERE ts_code = '000300.SH'
        ORDER BY trade_date
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date").sort_index()
    df["vol_30d"] = df["pct_chg"].rolling(30, min_periods=10).std() * np.sqrt(252)
    return df[["vol_30d"]]


# ── Indicator 4: Trading Volume ──

def compute_volume() -> pd.DataFrame:
    """全市场成交额 (SZ+SH 求和)."""
    sql = """
        SELECT trade_date, SUM(amount) as total_amount
        FROM raw_daily_info
        WHERE exchange IN ('SH', 'SZ')
        GROUP BY trade_date
        ORDER BY trade_date
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date").sort_index()
    df["amount"] = df["total_amount"]
    return df[["amount"]]


# ── Indicator 5: Margin Sentiment ──

def compute_margin_sentiment() -> pd.DataFrame:
    """融资买入额占全市场成交额比例."""
    sql_margin = """
        SELECT trade_date, SUM(rzmre) as margin_buy
        FROM raw_margin_detail
        GROUP BY trade_date
        ORDER BY trade_date
    """
    sql_amount = """
        SELECT trade_date, SUM(amount) as total_amount
        FROM raw_daily_info
        WHERE exchange IN ('SH', 'SZ')
        GROUP BY trade_date
        ORDER BY trade_date
    """
    with db_session() as s:
        m = pd.read_sql(text(sql_margin), s.bind)
        a = pd.read_sql(text(sql_amount), s.bind)
    m["trade_date"] = pd.to_datetime(m["trade_date"])
    a["trade_date"] = pd.to_datetime(a["trade_date"])
    df = m.merge(a, on="trade_date", how="inner")
    df = df.set_index("trade_date").sort_index()
    df["margin_ratio"] = df["margin_buy"] / df["total_amount"] * 100
    return df[["margin_ratio"]]


# ── Indicator 6: Limit Up/Down Ratio ──

def compute_limit_ratio() -> pd.DataFrame:
    """涨停数占比: Z_count / (Z_count + D_count)."""
    sql = """
        SELECT trade_date, lim, COUNT(*) as cnt
        FROM raw_limit_list_d
        WHERE lim IN ('Z', 'D')
        GROUP BY trade_date, lim
        ORDER BY trade_date
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    pivot = df.pivot(index="trade_date", columns="lim", values="cnt").fillna(0)
    pivot["limit_ratio"] = pivot["Z"] / (pivot["Z"] + pivot["D"]) * 100
    return pivot[["limit_ratio"]]


# ── Indicator 7: Northbound Flow ──

def compute_northbound() -> pd.DataFrame:
    """北向资金 20日净买入 Z-Score + 连续流入奖励."""
    sql = """
        SELECT trade_date, north_money
        FROM raw_moneyflow_hsgt
        ORDER BY trade_date
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date").sort_index()
    # Daily net flow from cumulative
    df["net_flow"] = df["north_money"].diff()
    # 20-day rolling net
    df["net_20d"] = df["net_flow"].rolling(20, min_periods=5).sum()
    # Z-score
    df["north_z"] = _rolling_zscore(df["net_20d"], 252)
    # Map Z-score [-3,3] → [0,100]
    df["north_score"] = ((df["north_z"].clip(-3, 3) + 3) / 6 * 100)
    return df[["north_score"]]


# ── Indicator 8: Turnover Rate ──

def compute_turnover() -> pd.DataFrame:
    """全市场换手率 (按 float_mv 加权)."""
    sql = """
        SELECT trade_date,
               SUM(tr * float_mv) / NULLIF(SUM(float_mv), 0) as weighted_tr
        FROM raw_daily_info
        WHERE exchange IN ('SH', 'SZ') AND tr IS NOT NULL AND float_mv > 0
        GROUP BY trade_date
        ORDER BY trade_date
    """
    with db_session() as s:
        df = pd.read_sql(text(sql), s.bind)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date").sort_index()
    return df[["weighted_tr"]]
