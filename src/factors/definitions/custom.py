"""自定义代码因子 — 需要 Python 实现的复杂因子

用 impl="code" 注册，compute 函数接收 Polars DataFrame，返回 Series。
"""

import polars as pl
from src.factors.registry import register_factor


# ═══════════════════════════════════════════
# 技术指标 (需要多步骤计算)
# ═══════════════════════════════════════════

@register_factor("tech", "kdj_k", impl="code")
def kdj_k(df: pl.DataFrame) -> pl.Series:
    """KDJ 指标的 K 值 (9,3,3)。

    RSV = (close - low_9) / (high_9 - low_9) * 100
    K = EMA(RSV, 3)
    """
    low_9 = df["low"].rolling_min(window_size=9).over("ts_code")
    high_9 = df["high"].rolling_max(window_size=9).over("ts_code")
    rsv = ((df["close"] - low_9) / (high_9 - low_9).fill_null(1)) * 100.0
    return rsv.ewm_mean(span=3, min_periods=3)


@register_factor("tech", "kdj_d", impl="code")
def kdj_d(df: pl.DataFrame) -> pl.Series:
    """KDJ 指标的 D 值: EMA(K, 3)。"""
    k = kdj_k(df)
    return k.ewm_mean(span=3, min_periods=3)


@register_factor("tech", "kdj_j", impl="code")
def kdj_j(df: pl.DataFrame) -> pl.Series:
    """KDJ 指标的 J 值: 3*K - 2*D。"""
    k = kdj_k(df)
    d = kdj_d(df)
    return 3 * k - 2 * d


@register_factor("tech", "obv", impl="code")
def obv(df: pl.DataFrame) -> pl.Series:
    """能量潮 OBV。

    OBV_t = OBV_{t-1} + volume * sign(close - pre_close)
    """
    # Per-stock computation needed
    result = df.sort(["ts_code", "trade_date"]).with_columns(
        pl.when(pl.col("close") > pl.col("close").shift(1).over("ts_code"))
        .then(pl.col("volume"))
        .when(pl.col("close") < pl.col("close").shift(1).over("ts_code"))
        .then(-pl.col("volume"))
        .otherwise(0)
        .alias("_direction")
    )
    return result.with_columns(
        pl.col("_direction").cum_sum().over("ts_code").alias("obv")
    )["obv"]


# ═══════════════════════════════════════════
# 波动率 — GARCH-style
# ═══════════════════════════════════════════

@register_factor("volatility", "parkinson_vol_20d", impl="code")
def parkinson_vol_20d(df: pl.DataFrame) -> pl.Series:
    """Parkinson 波动率 (使用 high-low 范围)。

    sigma^2 = (1 / (4*ln(2)*N)) * sum(log(high/low))^2
    """
    log_hl = (pl.col("high") / pl.col("low")).log()
    return (
        (log_hl.pow(2) / (4 * 1.3863))
        .rolling_sum(window_size=20, min_periods=5)
        .sqrt()
        .over("ts_code")
    )


@register_factor("volatility", "yang_zhang_vol_20d", impl="code")
def yang_zhang_vol_20d(df: pl.DataFrame) -> pl.Series:
    """Yang-Zhang 波动率 (结合 overnight + intraday)。

    sigma_yz^2 = sigma_o^2 + k * sigma_c^2 + (1-k) * sigma_rs^2
    """
    # overnight return: log(open / pre_close)
    close_prev = df["close"].shift(1).over("ts_code")
    ret_overnight = (df["open"] / close_prev.fill_null(df["open"])).log()
    # intraday return: log(close / open)
    ret_close = (df["close"] / df["open"]).log()

    r = 20
    so = ret_overnight.rolling_std(window_size=r, min_periods=5)
    sc = ret_close.rolling_std(window_size=r, min_periods=5)

    k = 0.34 / (1.34 + (r + 1) / (r - 1))
    return (so.pow(2) + k * sc.pow(2)).sqrt()


# ═══════════════════════════════════════════
# 资金流 — 情绪
# ═══════════════════════════════════════════

@register_factor("sentiment", "moneyflow_pct_5d", impl="code")
def moneyflow_pct_5d(df: pl.DataFrame) -> pl.Series:
    """5日累计主力净流入 / 流通市值。

    需要 df 中有 main_net (主力净流入) 列。
    """
    if "main_net" not in df.columns:
        raise ValueError("Column 'main_net' required for moneyflow_pct_5d")

    return (
        pl.col("main_net")
        .rolling_sum(window_size=5, min_periods=1)
        .over("ts_code")
        / pl.col("float_mv").fill_null(1e10)
    )
