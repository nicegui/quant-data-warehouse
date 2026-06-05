"""Alpha158 价量因子 — Qlib Alpha158 完整实现.

158个因子 = 9 K线形态 + 4 价格比 + 145 滚动算子 (29操作 × 5窗口).

使用:
    from src.factors.alpha158 import compute_all_alpha158
    results = compute_all_alpha158()  # 返回 {name: DataFrame} 158个因子
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from functools import lru_cache
from typing import Optional

from src.factors.data import read_ohlcv
from src.factors.utils import process_factor

# ── 常量 ──
WINDOWS = [5, 10, 20, 30, 60]
EPS = 1e-12


# ═══════════════════════════════════════════════════════════
# 数据加载 (缓存，所有因子共享)
# ═══════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _load_ohlcv(start_date=None, end_date=None) -> dict:
    """加载全量 OHLCV + VWAP，带缓存."""
    return read_ohlcv(start_date, end_date)


def _get_wide(ohlcv: dict, field: str) -> pd.DataFrame:
    """取 pivot DataFrame."""
    return ohlcv.get(field, pd.DataFrame())


# ═══════════════════════════════════════════════════════════
# 1. Kbar — K线形态因子 (9个)
# ═══════════════════════════════════════════════════════════

def kmid(open_, close) -> pd.DataFrame:
    """($close - $open) / $open"""
    return (close - open_) / open_.replace(0, np.nan)


def klen(open_, high, low) -> pd.DataFrame:
    """($high - $low) / $open"""
    return (high - low) / open_.replace(0, np.nan)


def kmid2(open_, high, low, close) -> pd.DataFrame:
    """($close - $open) / ($high - $low + ε)"""
    return (close - open_) / (high - low + EPS)


def kup(open_, high, close) -> pd.DataFrame:
    """($high - max($open, $close)) / $open"""
    return (high - np.maximum(open_, close)) / open_.replace(0, np.nan)


def kup2(open_, high, low, close) -> pd.DataFrame:
    """($high - max($open, $close)) / ($high - $low + ε)"""
    return (high - np.maximum(open_, close)) / (high - low + EPS)


def klow(open_, low, close) -> pd.DataFrame:
    """(min($open, $close) - $low) / $open"""
    return (np.minimum(open_, close) - low) / open_.replace(0, np.nan)


def klow2(open_, high, low, close) -> pd.DataFrame:
    """(min($open, $close) - $low) / ($high - $low + ε)"""
    return (np.minimum(open_, close) - low) / (high - low + EPS)


def ksft(open_, high, low, close) -> pd.DataFrame:
    """(2*$close - $high - $low) / $open"""
    return (2 * close - high - low) / open_.replace(0, np.nan)


def ksft2(open_, high, low, close) -> pd.DataFrame:
    """(2*$close - $high - $low) / ($high - $low + ε)"""
    return (2 * close - high - low) / (high - low + EPS)


KBAR_FACTORIES = [
    ("KMID",   lambda d: kmid(d['open'], d['close'])),
    ("KLEN",   lambda d: klen(d['open'], d['high'], d['low'])),
    ("KMID2",  lambda d: kmid2(d['open'], d['high'], d['low'], d['close'])),
    ("KUP",    lambda d: kup(d['open'], d['high'], d['close'])),
    ("KUP2",   lambda d: kup2(d['open'], d['high'], d['low'], d['close'])),
    ("KLOW",   lambda d: klow(d['open'], d['low'], d['close'])),
    ("KLOW2",  lambda d: klow2(d['open'], d['high'], d['low'], d['close'])),
    ("KSFT",   lambda d: ksft(d['open'], d['high'], d['low'], d['close'])),
    ("KSFT2",  lambda d: ksft2(d['open'], d['high'], d['low'], d['close'])),
]


# ═══════════════════════════════════════════════════════════
# 2. Price — 原始价格比 (4个)  OPEN0, HIGH0, LOW0, VWAP0
# ═══════════════════════════════════════════════════════════

PRICE_FACTORIES = [
    ("OPEN0",  lambda d: d['open'] / d['close'].replace(0, np.nan)),
    ("HIGH0",  lambda d: d['high'] / d['close'].replace(0, np.nan)),
    ("LOW0",   lambda d: d['low'] / d['close'].replace(0, np.nan)),
    ("VWAP0",  lambda d: d['vwap'] / d['close'].replace(0, np.nan)),
]


# ═══════════════════════════════════════════════════════════
# 3. Rolling — 滚动算子 (29个 × 5窗口 = 145个)
# ═══════════════════════════════════════════════════════════

def _rank_cross_sectional(df: pd.DataFrame) -> pd.DataFrame:
    """截面排名 (0~1)."""
    return df.rank(axis=1, pct=True)


def _slope(y: np.ndarray) -> float:
    """OLS斜率."""
    n = len(y)
    x = np.arange(n, dtype=float)
    xm, ym = x.mean(), y.mean()
    num = ((x - xm) * (y - ym)).sum()
    den = ((x - xm) ** 2).sum()
    return num / den if den != 0 else 0.0


def _rsquared(y: np.ndarray) -> float:
    """OLS R²."""
    n = len(y)
    x = np.arange(n, dtype=float)
    xm, ym = x.mean(), y.mean()
    num = ((x - xm) * (y - ym)).sum()
    den_x = ((x - xm) ** 2).sum()
    den_y = ((y - ym) ** 2).sum()
    if den_x == 0 or den_y == 0:
        return 0.0
    r = num / np.sqrt(den_x * den_y)
    return r ** 2


def _residual(y: np.ndarray) -> float:
    """OLS残差 (最后一点)."""
    n = len(y)
    x = np.arange(n, dtype=float)
    slope = _slope(y)
    intercept = y.mean() - slope * x.mean()
    predicted = slope * x[-1] + intercept
    return y[-1] - predicted


def make_rolling_factories() -> list[tuple[str, callable]]:
    """构建所有 145 个滚动因子工厂."""
    factories = []

    for w in WINDOWS:
        w = int(w)

        # ── 1. ROC: close / Ref(close, d) - 1 ──
        factories.append((f"ROC{w}",
            lambda d, w=w: d['close'].pct_change(w).shift(1)))

        # ── 2. MA: Mean(close, d) / close ──
        factories.append((f"MA{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).mean() / d['close'].replace(0, np.nan)))

        # ── 3. STD: Std(close, d) / close ──
        factories.append((f"STD{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).std() / d['close'].replace(0, np.nan)))

        # ── 4. BETA: Slope(close, d) / close ──
        factories.append((f"BETA{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).apply(_slope, raw=True) / d['close'].replace(0, np.nan)))

        # ── 5. RSQR: Rsquare(close, d) ──
        factories.append((f"RSQR{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).apply(_rsquared, raw=True)))

        # ── 6. RESI: Resi(close, d) / close ──
        factories.append((f"RESI{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).apply(_residual, raw=True) / d['close'].replace(0, np.nan)))

        # ── 7. MAX: Max(high, d) / close ──
        factories.append((f"MAX{w}",
            lambda d, w=w: d['high'].rolling(w, min_periods=max(5, w//2)).max() / d['close'].replace(0, np.nan)))

        # ── 8. MIN: Min(low, d) / close ──
        factories.append((f"MIN{w}",
            lambda d, w=w: d['low'].rolling(w, min_periods=max(5, w//2)).min() / d['close'].replace(0, np.nan)))

        # ── 9. QTLU: Quantile(close, d, 0.8) / close ──
        factories.append((f"QTLU{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).quantile(0.8) / d['close'].replace(0, np.nan)))

        # ── 10. QTLD: Quantile(close, d, 0.2) / close ──
        factories.append((f"QTLD{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).quantile(0.2) / d['close'].replace(0, np.nan)))

        # ── 11. RANK: Rank(close, d) — 截面排名 ──
        factories.append((f"RANK{w}",
            lambda d, w=w: _rank_cross_sectional(
                d['close'].rolling(w, min_periods=max(5, w//2)).mean())))

        # ── 12. RSV: (close-Min(low,d)) / (Max(high,d)-Min(low,d)+ε) ──
        factories.append((f"RSV{w}",
            lambda d, w=w: (d['close'] - d['low'].rolling(w, min_periods=max(5, w//2)).min()) /
                           (d['high'].rolling(w, min_periods=max(5, w//2)).max() -
                            d['low'].rolling(w, min_periods=max(5, w//2)).min() + EPS)))

        # ── 13. IMAX: IdxMax(high, d) / d ──
        factories.append((f"IMAX{w}",
            lambda d, w=w: d['high'].rolling(w, min_periods=max(5, w//2)).apply(
                lambda x: np.argmax(x) if len(x) > 0 else 0, raw=True) / w))

        # ── 14. IMIN: IdxMin(low, d) / d ──
        factories.append((f"IMIN{w}",
            lambda d, w=w: d['low'].rolling(w, min_periods=max(5, w//2)).apply(
                lambda x: np.argmin(x) if len(x) > 0 else 0, raw=True) / w))

        # ── 15. IMXD: (IdxMax(high,d) - IdxMin(low,d)) / d ──
        factories.append((f"IMXD{w}",
            lambda d, w=w: (
                d['high'].rolling(w, min_periods=max(5, w//2)).apply(lambda x: np.argmax(x) if len(x)>0 else 0, raw=True) -
                d['low'].rolling(w, min_periods=max(5, w//2)).apply(lambda x: np.argmin(x) if len(x)>0 else 0, raw=True)
            ) / w))

        # ── 16. CORR: Corr(close, Log(volume+1), d) ──
        factories.append((f"CORR{w}",
            lambda d, w=w: d['close'].rolling(w, min_periods=max(5, w//2)).corr(
                np.log(d['volume'] + 1))))

        # ── 17. CORD: Corr(close_ret, Log(volume_ret+1), d) ──
        factories.append((f"CORD{w}",
            lambda d, w=w: d['close'].pct_change().rolling(w, min_periods=max(5, w//2)).corr(
                np.log(d['volume'].pct_change().abs() + 1))))

        # ── 18. CNTP: Mean(close>Ref(close,1), d) — 上涨天数占比 ──
        factories.append((f"CNTP{w}",
            lambda d, w=w: d['close'].diff().gt(0).rolling(w, min_periods=max(5, w//2)).mean()))

        # ── 19. CNTN: Mean(close<Ref(close,1), d) — 下跌天数占比 ──
        factories.append((f"CNTN{w}",
            lambda d, w=w: d['close'].diff().lt(0).rolling(w, min_periods=max(5, w//2)).mean()))

        # ── 20. CNTD: CNTP - CNTN ──
        factories.append((f"CNTD{w}",
            lambda d, w=w: d['close'].diff().gt(0).rolling(w, min_periods=max(5, w//2)).mean() -
                           d['close'].diff().lt(0).rolling(w, min_periods=max(5, w//2)).mean()))

        # ── 21. SUMP: UpsideSum / TotalAbsSum ──
        factories.append((f"SUMP{w}",
            lambda d, w=w: (d['close'].diff().clip(lower=0).rolling(w, min_periods=max(5, w//2)).sum() /
                           (d['close'].diff().abs().rolling(w, min_periods=max(5, w//2)).sum() + EPS))))

        # ── 22. SUMN: DownsideSum / TotalAbsSum ──
        factories.append((f"SUMN{w}",
            lambda d, w=w: (d['close'].diff().clip(upper=0).abs().rolling(w, min_periods=max(5, w//2)).sum() /
                           (d['close'].diff().abs().rolling(w, min_periods=max(5, w//2)).sum() + EPS))))

        # ── 23. SUMD: (UpsideSum - DownsideSum) / TotalAbsSum ──
        factories.append((f"SUMD{w}",
            lambda d, w=w: (d['close'].diff().rolling(w, min_periods=max(5, w//2)).sum() /
                           (d['close'].diff().abs().rolling(w, min_periods=max(5, w//2)).sum() + EPS))))

        # ── 24. VMA: Mean(volume, d) / (volume + ε) ──
        factories.append((f"VMA{w}",
            lambda d, w=w: d['volume'].rolling(w, min_periods=max(5, w//2)).mean() /
                           (d['volume'] + EPS)))

        # ── 25. VSTD: Std(volume, d) / (volume + ε) ──
        factories.append((f"VSTD{w}",
            lambda d, w=w: d['volume'].rolling(w, min_periods=max(5, w//2)).std() /
                           (d['volume'] + EPS)))

        # ── 26. WVMA: Std(abs_ret*vol, d) / Mean(abs_ret*vol, d) ──
        factories.append((f"WVMA{w}",
            lambda d, w=w: (
                (d['close'].pct_change().abs() * d['volume']).rolling(w, min_periods=max(5, w//2)).std() /
                ((d['close'].pct_change().abs() * d['volume']).rolling(w, min_periods=max(5, w//2)).mean() + EPS))))

        # ── 27. VSUMP: VolUpSum / TotalVolAbsSum ──
        factories.append((f"VSUMP{w}",
            lambda d, w=w: (d['volume'].diff().clip(lower=0).rolling(w, min_periods=max(5, w//2)).sum() /
                           (d['volume'].diff().abs().rolling(w, min_periods=max(5, w//2)).sum() + EPS))))

        # ── 28. VSUMN: VolDownSum / TotalVolAbsSum ──
        factories.append((f"VSUMN{w}",
            lambda d, w=w: (d['volume'].diff().clip(upper=0).abs().rolling(w, min_periods=max(5, w//2)).sum() /
                           (d['volume'].diff().abs().rolling(w, min_periods=max(5, w//2)).sum() + EPS))))

        # ── 29. VSUMD: (VolUpSum - VolDownSum) / TotalVolAbsSum ──
        factories.append((f"VSUMD{w}",
            lambda d, w=w: (d['volume'].diff().rolling(w, min_periods=max(5, w//2)).sum() /
                           (d['volume'].diff().abs().rolling(w, min_periods=max(5, w//2)).sum() + EPS))))

    return factories


# ═══════════════════════════════════════════════════════════
# 单因子计算函数 (兼容 compute_factor 接口)
# ═══════════════════════════════════════════════════════════

def _compute_single(name: str, factory: callable,
                    start_date=None, end_date=None) -> pd.DataFrame:
    """计算单个 alpha158 因子."""
    ohlcv = _load_ohlcv(start_date, end_date)
    df = factory(ohlcv)
    if df.empty:
        return df
    return process_factor(df.replace([np.inf, -np.inf], np.nan))


# ═══════════════════════════════════════════════════════════
# 批量计算 + 返回注册表
# ═══════════════════════════════════════════════════════════

def compute_all_alpha158(start_date=None, end_date=None,
                         categories: list[str] | None = None
                         ) -> dict[str, pd.DataFrame]:
    """一次性计算全部 158 个因子 (数据只加载一次).

    Args:
        categories: 子集过滤. None = 全部. 
                    可选: ['kbar', 'price', 'rolling']

    Returns:
        {factor_name: DataFrame} 158个因子
    """
    print("Loading OHLCV data...")
    ohlcv = _load_ohlcv(start_date, end_date)
    if not ohlcv.get('close', pd.DataFrame()).size:
        print("ERROR: No OHLCV data loaded")
        return {}

    all_factories = []

    if categories is None or 'kbar' in categories:
        all_factories.extend(KBAR_FACTORIES)
    if categories is None or 'price' in categories:
        all_factories.extend(PRICE_FACTORIES)
    if categories is None or 'rolling' in categories:
        all_factories.extend(make_rolling_factories())

    results = {}
    n = len(all_factories)
    for i, (name, factory) in enumerate(all_factories):
        print(f"  [{i+1:3d}/{n}] {name} ...", end=" ")
        try:
            df = factory(ohlcv)
            if df.empty:
                print("EMPTY")
                results[name] = df
            else:
                df = process_factor(df.replace([np.inf, -np.inf], np.nan))
                results[name] = df
                print(f"{df.shape[0]}d × {df.shape[1]}s")
        except Exception as e:
            print(f"ERROR: {e}")
            results[name] = pd.DataFrame()

    return results


def build_registry() -> dict:
    """构建 FACTOR_REGISTRY 条目 (供 __init__.py 使用)."""
    registry = {}

    for name, factory in KBAR_FACTORIES:
        registry[name] = (factory, "alpha158", f"Alpha158 Kbar: {name}")

    for name, factory in PRICE_FACTORIES:
        registry[name] = (factory, "alpha158", f"Alpha158 Price: {name}")

    for name, factory in make_rolling_factories():
        # Extract description from name
        base = name.rstrip('0123456789')
        window = name[len(base):]
        registry[name] = (factory, "alpha158", f"Alpha158 Rolling: {base} {window}d")

    return registry
