"""因子库 — 标准化初级因子.

使用:
    from src.factors import compute_factor, list_factors, compute_all

架构:
    src/factors/value.py       — 估值(pe_ttm, pb_lf, ...)
    src/factors/momentum.py    — 动量(ret_1m, ret_12m_1m, ...)
    src/factors/volatility.py  — 波动(vol_1m, beta_1y, ...)
    src/factors/quality.py     — 质量(roe_ttm, gross_margin, ...)
    src/factors/growth.py      — 成长(revenue_growth_yoy, ...)
    src/factors/sentiment.py   — 情绪(xq_attention, ...)
    src/factors/liquidity.py   — 流动性(ln_cap, turnover_1m, ...)
    src/factors/macro_state.py — 宏观(market_pe_pct, bdi_momentum, ...)
"""

from __future__ import annotations
import pandas as pd
from typing import Callable, Optional

from src.factors import value, momentum, volatility, quality, growth, sentiment, liquidity, macro_state
from src.factors.utils import save_factor


# ── 因子注册表 ──
FACTOR_REGISTRY: dict[str, tuple[Callable, str, str]] = {
    # (计算函数, 类别, 描述)
    # Value
    "pe_ttm":              (value.pe_ttm,              "value",      "市盈率倒数(TTM)"),
    "pb_lf":               (value.pb_lf,               "value",      "市净率倒数"),
    "ep_ttm":              (value.ep_ttm,              "value",      "盈利收益率"),
    "sp_ttm":              (value.sp_ttm,              "value",      "市销率倒数"),
    "div_yield":           (value.div_yield,           "value",      "股息率"),
    # Momentum
    "ret_1m":              (momentum.ret_1m,           "momentum",   "1月动量(跳过1天)"),
    "ret_3m":              (momentum.ret_3m,           "momentum",   "3月动量"),
    "ret_6m":              (momentum.ret_6m,           "momentum",   "6月动量"),
    "ret_12m_1m":          (momentum.ret_12m_1m,       "momentum",   "12-1月动量"),
    "ret_1m_reverse":      (momentum.ret_1m_reverse,   "momentum",   "短期反转"),
    "max_ret_1m":          (momentum.max_ret_1m,       "momentum",   "月最大日收益"),
    # Volatility
    "vol_1m":              (volatility.vol_1m,         "volatility", "1月波动率"),
    "vol_3m":              (volatility.vol_3m,         "volatility", "3月波动率"),
    "downside_vol_1m":     (volatility.downside_vol_1m,"volatility", "下行波动率"),
    "skew_1m":             (volatility.skew_1m,        "volatility", "收益偏度"),
    "beta_1y":             (volatility.beta_1y,        "volatility", "1年Beta(对300)"),
    "idiosyncratic_vol":   (volatility.idiosyncratic_vol, "volatility", "特质波动率"),
    # Quality
    "roe_ttm":             (quality.roe_ttm,           "quality",    "ROE(TTM)"),
    "roa_ttm":             (quality.roa_ttm,           "quality",    "ROA(TTM)"),
    "gross_margin":        (quality.gross_margin,      "quality",    "毛利率"),
    "net_margin":          (quality.net_margin,        "quality",    "净利率"),
    "debt_to_assets":      (quality.debt_to_assets,    "quality",    "资产负债率倒数"),
    "earnings_stability":  (quality.earnings_stability,"quality",    "盈利稳定性"),
    # Growth
    "revenue_growth_yoy":  (growth.revenue_growth_yoy, "growth",     "营收同比增长"),
    "earnings_growth_yoy": (growth.earnings_growth_yoy,"growth",     "净利润同比增长"),
    # Sentiment
    "xq_attention":        (sentiment.xq_attention,    "sentiment",  "雪球关注(对数)"),
    "xq_discussion":       (sentiment.xq_discussion,   "sentiment",  "雪球讨论(对数)"),
    "xq_deal_heat":        (sentiment.xq_deal_heat,    "sentiment",  "雪球交易热度"),
    "xq_attention_delta_1w":(sentiment.xq_attention_delta_1w, "sentiment", "关注度周变化⭐"),
    "weibo_sentiment":     (sentiment.weibo_sentiment,  "sentiment",  "微博情绪"),
    # Liquidity
    "ln_market_cap":       (liquidity.ln_market_cap,   "liquidity",  "对数总市值"),
    "turnover_1m":         (liquidity.turnover_1m,     "liquidity",  "月均换手率"),
    "turnover_cv":         (liquidity.turnover_cv,     "liquidity",  "换手率变异"),
    "amihud_illiq":        (liquidity.amihud_illiq,    "liquidity",  "Amihud非流动性"),
    "dollar_volume_1m":    (liquidity.dollar_volume_1m,"liquidity",  "月均成交额"),
    # Macro
    "market_pe_pct":       (macro_state.market_pe_pct, "macro",      "沪深300 PE分位"),
    "cn_us_spread_10y":    (macro_state.cn_us_spread_10y, "macro",   "中美10Y利差"),
    "bdi_momentum":        (macro_state.bdi_momentum,  "macro",      "BDI 3月动量"),
    "qvix_level":          (macro_state.qvix_level,    "macro",      "QVIX恐慌指数"),
    "margin_balance_ratio":(macro_state.margin_balance_ratio, "macro","融资余额变化"),
}


def list_factors(category: Optional[str] = None) -> list[dict]:
    """列出所有因子."""
    result = []
    for name, (fn, cat, desc) in FACTOR_REGISTRY.items():
        if category and cat != category:
            continue
        result.append({"name": name, "category": cat, "description": desc})
    return result


def compute_factor(name: str, start_date=None, end_date=None, save: bool = False) -> pd.DataFrame:
    """计算单个因子."""
    if name not in FACTOR_REGISTRY:
        raise KeyError(f"Unknown factor: {name}. Use list_factors() to see available.")
    
    fn, cat, desc = FACTOR_REGISTRY[name]
    print(f"Computing {name} ({cat}): {desc} ...")
    df = fn(start_date=start_date, end_date=end_date)
    
    if save and not df.empty:
        save_factor(df, name)
        print(f"  Saved to data/factors/{name}.parquet")
    
    print(f"  Shape: {df.shape}, coverage: {df.notna().sum().sum()} values")
    return df


def compute_all(category=None, start_date=None, end_date=None, save=False) -> dict[str, pd.DataFrame]:
    """计算所有因子."""
    results = {}
    for name in FACTOR_REGISTRY:
        if category and FACTOR_REGISTRY[name][1] != category:
            continue
        try:
            results[name] = compute_factor(name, start_date, end_date, save)
        except Exception as e:
            print(f"  {name}: ERROR {e}")
    return results
