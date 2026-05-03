"""情绪/关注度因子."""

from __future__ import annotations
import numpy as np
import pandas as pd
from src.factors.data import read_macro_indicator, read_daily_basic
from src.factors.utils import process_factor


def _build_sentiment_df(source: str) -> pd.DataFrame:
    """从 raw_macro_indicator 构建 date × ts_code 矩阵."""
    df = read_macro_indicator([source])
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    pivot = df.pivot(index="date", columns="sub_key", values="value")
    pivot = pivot.sort_index()
    return pivot


def xq_attention(start_date=None, end_date=None) -> pd.DataFrame:
    """雪球关注数 (取对数)."""
    df = _build_sentiment_df("xq_hot_follow")
    if df.empty:
        return pd.DataFrame()
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]
    df = np.log(df.clip(lower=1))
    return process_factor(df)


def xq_discussion(start_date=None, end_date=None) -> pd.DataFrame:
    """雪球讨论数 (取对数)."""
    df = _build_sentiment_df("xq_hot_tweet")
    if df.empty:
        return pd.DataFrame()
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]
    df = np.log(df.clip(lower=1))
    return process_factor(df)


def xq_deal_heat(start_date=None, end_date=None) -> pd.DataFrame:
    """雪球交易热度."""
    df = _build_sentiment_df("xq_hot_deal")
    if df.empty:
        return pd.DataFrame()
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]
    df = np.log(df.clip(lower=1))
    return process_factor(df)


def xq_attention_delta_1w(start_date=None, end_date=None) -> pd.DataFrame:
    """雪球关注度周变化 — 核心情绪alpha."""
    df = _build_sentiment_df("xq_hot_follow")
    if df.empty:
        return pd.DataFrame()
    df = np.log(df.clip(lower=1))
    delta = df.diff(5)
    if start_date:
        delta = delta[delta.index >= pd.Timestamp(start_date)]
    if end_date:
        delta = delta[delta.index <= pd.Timestamp(end_date)]
    return process_factor(delta)


def weibo_sentiment(start_date=None, end_date=None) -> pd.DataFrame:
    """微博情绪得分 (top 50 stock only)."""
    df = _build_sentiment_df("weibo_report")
    if df.empty:
        return pd.DataFrame()
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date)]
    return process_factor(df)
