"""因子表达式算子库

提供 Qlib-style 的时间序列算子。所有算子操作 Polars Series/Expr。

两种使用方式：
1. 表达式引擎解析字符串 → 调用算子函数
2. 代码因子直接 import 调用
"""

from __future__ import annotations

import polars as pl
from typing import Optional


def _i(v: float) -> int:
    """Cast to int (handles float from AST parser)."""
    return int(v)


# ═══════════════════════════════════════════
# 基础算子
# ═══════════════════════════════════════════

def ref(series: pl.Series, n: float = 1) -> pl.Series:
    """滞后 N 期。Ref($close, -5) = 5天前收盘价。"""
    ni = _i(n)
    if ni >= 0:
        return series.shift(ni)
    return series.shift(-ni)


def delta(series: pl.Series, n: float = 1) -> pl.Series:
    """N 期差值。Delta($close, 5) = close - close.shift(5)。"""
    ni = _i(n)
    return series - ref(series, ni)


def pct_chg(series: pl.Series, n: float = 1) -> pl.Series:
    """N 期涨跌幅。PctChg($close, 5) = close / close.shift(5) - 1。"""
    ni = _i(n)
    shifted = ref(series, ni)
    return series / shifted - 1.0


# ═══════════════════════════════════════════
# 滚动统计算子
# ═══════════════════════════════════════════

def rolling_mean(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动均值。"""
    w = _i(window)
    return series.rolling_mean(window_size=w, min_periods=max(1, w // 2))


def rolling_std(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动标准差。"""
    w = _i(window)
    return series.rolling_std(window_size=w, min_periods=max(1, w // 2))


def rolling_max(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动最大值。"""
    w = _i(window)
    return series.rolling_max(window_size=w, min_periods=max(1, w // 2))


def rolling_min(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动最小值。"""
    w = _i(window)
    return series.rolling_min(window_size=w, min_periods=max(1, w // 2))


def rolling_sum(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动求和。"""
    w = _i(window)
    return series.rolling_sum(window_size=w, min_periods=max(1, w // 2))


def rolling_skew(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动偏度。"""
    w = _i(window)
    mean = rolling_mean(series, w)
    std = rolling_std(series, w)
    return ((series - mean) ** 3).rolling_mean(window_size=w, min_periods=max(1, w // 2)) / (std ** 3)


def rolling_kurt(series: pl.Series, window: float) -> pl.Series:
    """N 期滚动峰度。"""
    w = _i(window)
    mean = rolling_mean(series, w)
    std = rolling_std(series, w)
    return ((series - mean) ** 4).rolling_mean(window_size=w, min_periods=max(1, w // 2)) / (std ** 4)


# ═══════════════════════════════════════════
# 相关性算子
# ═══════════════════════════════════════════

def rolling_corr(a: pl.Series, b: pl.Series, window: float) -> pl.Series:
    """N 期滚动相关系数。"""
    w = _i(window)
    ma = rolling_mean(a, w)
    mb = rolling_mean(b, w)
    cov = ((a - ma) * (b - mb)).rolling_sum(window_size=w, min_periods=max(1, w // 2))
    sa = rolling_std(a, w)
    sb = rolling_std(b, w)
    return cov / (w * sa * sb)


# ═══════════════════════════════════════════
# 技术指标算子
# ═══════════════════════════════════════════

def ema(series: pl.Series, window: float) -> pl.Series:
    """指数移动平均。"""
    w = _i(window)
    return series.ewm_mean(span=w, min_periods=w)


def rsi(series: pl.Series, window: float = 14) -> pl.Series:
    """RSI 相对强弱指标。"""
    w = _i(window)
    diff = series.diff()
    gain = diff.clip(lower_bound=0)
    loss = (-diff).clip(lower_bound=0)
    avg_gain = gain.ewm_mean(span=w, min_periods=w)
    avg_loss = loss.ewm_mean(span=w, min_periods=w)
    rs = avg_gain / avg_loss.fill_null(1e-10)
    return 100.0 - (100.0 / (1.0 + rs))


def macd(
    series: pl.Series,
    fast: float = 12,
    slow: float = 26,
    signal: float = 9,
) -> dict[str, pl.Series]:
    """MACD — 返回 DIF, DEA, MACD_hist。"""
    f, sl, sg = _i(fast), _i(slow), _i(signal)
    ema_fast = ema(series, f)
    ema_slow = ema(series, sl)
    dif = ema_fast - ema_slow
    dea = ema(dif, sg)
    return {"DIF": dif, "DEA": dea, "MACD": 2 * (dif - dea)}


def sma(series: pl.Series, window: float) -> pl.Series:
    """简单移动平均。"""
    return rolling_mean(series, window)


# ═══════════════════════════════════════════
# 截面算子 (per-date)
# ═══════════════════════════════════════════

def cs_rank(df: pl.DataFrame, col: str, date_col: str = "trade_date") -> pl.Series:
    """截面排名 (0~1)。Rank($close) = 当日收盘价排名百分位。"""
    return (
        df.select([date_col, col])
        .with_columns(
            pl.col(col).rank("ordinal").over(date_col) / pl.col(col).count().over(date_col)
        )
        .get_column(col)
    )


def cs_scale(df: pl.DataFrame, col: str, date_col: str = "trade_date") -> pl.Series:
    """截面标准化 (z-score)。"""
    return (
        df.select([date_col, col])
        .with_columns(
            ((pl.col(col) - pl.col(col).mean().over(date_col))
             / pl.col(col).std().over(date_col))
        )
        .get_column(col)
    )


# ═══════════════════════════════════════════
# 算子映射表 (表达式引擎使用)
# ═══════════════════════════════════════════

OPERATOR_MAP: dict[str, tuple[callable, bool]] = {
    "Ref": (ref, False),
    "Delta": (delta, False),
    "PctChg": (pct_chg, False),
    "Mean": (rolling_mean, False),
    "Std": (rolling_std, False),
    "Max": (rolling_max, False),
    "Min": (rolling_min, False),
    "Sum": (rolling_sum, False),
    "Skew": (rolling_skew, False),
    "Kurt": (rolling_kurt, False),
    "Corr": (rolling_corr, False),
    "RSI": (rsi, False),
    "MACD": (macd, False),
    "EMA": (ema, False),
    "SMA": (sma, False),
    "Rank": (cs_rank, True),
    "Scale": (cs_scale, True),
}
