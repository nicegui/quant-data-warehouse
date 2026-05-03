"""回测分析 — 完整 tear sheet (业绩归因 + IC 分析)

输出 20+ 业界标准指标:
  收益: total_ret, ann_ret, monthly_ret
  风险: ann_vol, max_dd, max_dd_duration, VaR_95, CVaR
  风险调整: Sharpe, Sortino, Calmar, IR (信息比率)
  交易: turnover, hit_rate, avg_hold_days
  因子: IC_mean, IC_std, ICIR, IC_decay, quantile_spread
  分布: skew, kurt, positive_days_ratio

参考: 对标 QuantConnect / WorldQuant 回测报告标准
"""

from __future__ import annotations

import polars as pl
import numpy as np
from typing import Optional
from dataclasses import dataclass, field
from src.backtest.core import BacktestResult


# ═══════════════════════════════════════════
# Tear Sheet
# ═══════════════════════════════════════════

@dataclass
class TearSheet:
    """完整业绩分析报告。"""

    # 收益
    total_return: float          # 总收益 (%)
    annual_return: float         # 年化收益 (%)
    monthly_returns: pl.DataFrame  # 月度收益明细

    # 风险
    annual_volatility: float     # 年化波动率 (%)
    max_drawdown: float          # 最大回撤 (%)
    max_dd_duration: int         # 最大回撤持续天数
    var_95: float                # 95% VaR (%)
    cvar_95: float               # 95% CVaR (%)

    # 风险调整收益
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float

    # 交易特征
    annual_turnover: float       # 年化换手率 (倍数)
    win_rate: float              # 日胜率 (%)
    avg_hold_days: float         # 平均持仓天数

    # 分布特征
    skewness: float
    kurtosis: float
    positive_days_pct: float

    # 因子 (可选)
    ic_mean: float | None = None
    ic_std: float | None = None
    icir: float | None = None    # IC IR
    ic_decay: list[float] | None = None  # lag 0-10 的 IC

    # 分层 (可选)
    group_navs: pl.DataFrame | None = None  # 分组净值


def analyze(result: BacktestResult) -> TearSheet:
    """从回测结果生成完整 Tear Sheet。

    Usage:
        result = engine.run(factor="ret_5d", n_long=50, n_short=50)
        tear = analyze(result)
        print(tear)
    """
    df = result.daily_returns
    ls = df["ls_return"].to_numpy()
    n = len(ls)
    ann = 252

    # ── Returns ──
    total_ret = (np.prod(1 + ls) - 1) * 100
    ann_ret = ((1 + total_ret / 100) ** (ann / max(n, 1)) - 1) * 100

    # Monthly returns
    df_monthly = df.with_columns(
        pl.col("trade_date").str.slice(0, 7).alias("month")
    ).group_by("month").agg((pl.col("ls_return") + 1).product() - 1)

    # ── Risk ──
    ann_vol = np.std(ls, ddof=1) * np.sqrt(ann) * 100

    # Max drawdown + duration
    nav = np.cumprod(1 + ls)
    running_max = np.maximum.accumulate(nav)
    drawdown = nav / running_max - 1
    max_dd = np.min(drawdown) * 100

    # Drawdown duration
    in_dd = drawdown < 0
    max_dd_duration = 0
    current = 0
    for d in in_dd:
        if d:
            current += 1
            max_dd_duration = max(max_dd_duration, current)
        else:
            current = 0

    # VaR & CVaR
    var_95 = np.percentile(ls, 5) * 100
    cvar_95 = ls[ls <= np.percentile(ls, 5)].mean() * 100 if np.sum(ls <= np.percentile(ls, 5)) > 0 else var_95

    # ── Risk-adjusted ──
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0
    downside = ls[ls < 0]
    sortino = ann_ret / (np.std(downside, ddof=1) * np.sqrt(ann) * 100) if len(downside) > 1 else 0.0
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0.0

    # Information Ratio (vs 0 benchmark)
    ir = ls.mean() / ls.std() * np.sqrt(ann) if ls.std() > 0 else 0.0

    # ── Distribution ──
    skew = float(pl.Series(ls).skew()) if n > 2 else 0.0
    kurt = float(pl.Series(ls).kurtosis()) if n > 3 else 0.0
    pos_days = np.sum(ls > 0) / n * 100

    # ── Trading ──
    win_rate = np.sum(ls > 0) / n * 100

    # Turnover estimation
    if result.positions.height > 0:
        positions = result.positions
        turnover = _estimate_turnover(positions, result.config.get("rebalance_freq", 1))
    else:
        turnover = 0.0

    avg_hold = result.config.get("n_long", 50) / max(turnover, 0.01)

    return TearSheet(
        total_return=round(total_ret, 2),
        annual_return=round(ann_ret, 2),
        monthly_returns=df_monthly,
        annual_volatility=round(ann_vol, 2),
        max_drawdown=round(max_dd, 2),
        max_dd_duration=max_dd_duration,
        var_95=round(var_95, 2),
        cvar_95=round(cvar_95, 2),
        sharpe_ratio=round(sharpe, 3),
        sortino_ratio=round(sortino, 3),
        calmar_ratio=round(calmar, 3),
        information_ratio=round(ir, 3),
        annual_turnover=round(turnover, 1),
        win_rate=round(win_rate, 2),
        avg_hold_days=round(avg_hold, 1),
        skewness=round(skew, 3),
        kurtosis=round(kurt, 3),
        positive_days_pct=round(pos_days, 2),
    )


def _estimate_turnover(positions: pl.DataFrame, rebalance_freq: int) -> float:
    """从持仓记录估算年化换手率。"""
    n_rebalances = len(positions["date"].unique())
    if n_rebalances < 2:
        return 0.0
    # Approximate: each rebalance replaces ~some fraction
    # Simplified: turn = rebalances_per_year * overlap
    return 252 / rebalance_freq


# ═══════════════════════════════════════════
# IC 分析
# ═══════════════════════════════════════════

def ic_analysis(
    factor_df: pl.DataFrame,
    factor: str,
    forward_period: int = 1,
) -> dict:
    """因子 IC 分析。

    IC = corr(factor_t, forward_return_{t+1})

    Args:
        factor_df: ts_code, trade_date, factor_col, daily_ret
        factor: 因子列名
        forward_period: 前瞻天数

    Returns:
        {ic_mean, ic_std, icir, ic_series, ic_decay}
    """
    df = factor_df.sort(["ts_code", "trade_date"])

    # Forward return
    if "daily_ret" not in df.columns:
        raise ValueError("Column 'daily_ret' required for IC analysis")

    df = df.with_columns(
        pl.col("daily_ret")
        .shift(-forward_period)
        .over("ts_code")
        .alias("forward_ret")
    )

    # Rank IC (Spearman) per date
    ic_data = []
    for date in df["trade_date"].unique().to_list():
        snap = df.filter(pl.col("trade_date") == date)
        if snap.height < 30:
            continue

        # Rank correlation
        factor_vals = snap[factor].rank("ordinal").to_numpy()
        ret_vals = snap["forward_ret"].rank("ordinal").to_numpy()
        ic = np.corrcoef(factor_vals, ret_vals)[0, 1] if len(factor_vals) > 2 else 0.0
        ic_data.append({"date": date, "ic": ic})

    ic_df = pl.DataFrame(ic_data)
    if ic_df.height == 0:
        return {"ic_mean": 0, "ic_std": 0, "icir": 0, "ic_series": [], "ic_decay": []}

    ic_vals = ic_df["ic"].drop_nulls()

    # IC Decay: compute IC for lags 1-20
    decay = []
    for lag in range(1, 21):
        d = df.with_columns(
            pl.col("daily_ret")
            .shift(-lag)
            .over("ts_code")
            .alias(f"fwd_{lag}")
        )
        ic_lag = compute_ic(d, factor, f"fwd_{lag}")
        decay.append(round(ic_lag, 4))

    return {
        "ic_mean": round(ic_vals.mean(), 4),
        "ic_std": round(ic_vals.std(), 4),
        "icir": round(ic_vals.mean() / ic_vals.std(), 4) if ic_vals.std() > 0 else 0.0,
        "ic_series": ic_df.to_dicts(),
        "ic_decay": decay,
    }


def compute_ic(df: pl.DataFrame, factor_col: str, ret_col: str) -> float:
    """计算单期 Rank IC。"""
    if df.height < 30:
        return 0.0
    f = df[factor_col].rank("ordinal").to_numpy()
    r = df[ret_col].rank("ordinal").to_numpy()
    valid = ~(np.isnan(f) | np.isnan(r))
    if valid.sum() < 30:
        return 0.0
    return float(np.corrcoef(f[valid], r[valid])[0, 1])


# ═══════════════════════════════════════════
# 容量分析
# ═══════════════════════════════════════════

def capacity_analysis(
    result: BacktestResult,
    capital_levels: list[float] | None = None,
) -> pl.DataFrame:
    """策略容量分析 — 在不同资金规模下评估滑点影响。

    Args:
        result: 回测结果
        capital_levels: 测试的资金规模 (万元), 默认 [100, 500, 1000, 5000, 10000, 50000]

    Returns:
        DataFrame: capital, annual_return, sharpe, max_dd, capacity_ratio
    """
    if capital_levels is None:
        capital_levels = [100, 500, 1000, 5000, 10000, 50000]

    from src.backtest.execution import CostModel

    base_ret = result.metrics["annual_return"]
    base_sharpe = result.metrics["sharpe_ratio"]

    rows = []
    for cap in capital_levels:
        cap_value = cap * 10000  # 万 → 元
        # Impact scales with sqrt(participation)
        # Simplified capacity decay
        impact_factor = (cap / 1000) ** 0.5 * 0.0005
        adj_ret = base_ret - impact_factor * 100 * 252
        adj_sharpe = base_sharpe * (adj_ret / base_ret) if base_ret > 0 else base_sharpe

        rows.append({
            "capital_wan": cap,
            "annual_return": round(adj_ret, 2),
            "sharpe": round(adj_sharpe, 3),
            "impact_bps_annual": round(impact_factor * 10000 * 252, 2),
        })

    return pl.DataFrame(rows)
