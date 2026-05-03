"""Fear & Greed Index engine — merge indicators, score, synthesize."""

import logging
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

from src.research.fgi.indicators import (
    compute_price_momentum,
    compute_market_breadth,
    compute_volatility,
    compute_volume,
    compute_margin_sentiment,
    compute_limit_ratio,
    compute_northbound,
    compute_turnover,
    _rolling_pct_rank,
)

logger = logging.getLogger(__name__)

# Indicator definitions: (name, compute_fn, invert, weight)
INDICATORS = [
    ("price_momentum",   compute_price_momentum,   False, 0.125),
    ("market_breadth",   compute_market_breadth,   False, 0.125),
    ("volatility",       compute_volatility,       True,  0.125),
    ("volume",           compute_volume,           False, 0.125),
    ("margin_sentiment", compute_margin_sentiment, False, 0.125),
    ("limit_ratio",      compute_limit_ratio,      False, 0.125),
    ("northbound",       compute_northbound,       False, 0.125),
    ("turnover",         compute_turnover,         False, 0.125),
]


def _score_column(
    series: pd.Series, invert: bool = False, window: int = 252
) -> pd.Series:
    """Convert raw values to 0-100 scores via rolling percentile rank."""
    scores = _rolling_pct_rank(series, window)
    if invert:
        scores = 100 - scores
    return scores.clip(0, 100)


def _sentiment_label(fgi: float) -> str:
    if fgi <= 20:
        return "极度恐惧"
    elif fgi <= 40:
        return "恐惧"
    elif fgi <= 60:
        return "中性"
    elif fgi <= 80:
        return "贪婪"
    else:
        return "极度贪婪"


def _filter_trading_days(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to trading days using 000300.SH as calendar."""
    from src.db.session import db_session
    from sqlalchemy import text

    with db_session() as s:
        cal = pd.read_sql(
            text("SELECT DISTINCT trade_date FROM raw_index_daily WHERE ts_code='000300.SH'"),
            s.bind,
        )
    cal["trade_date"] = pd.to_datetime(cal["trade_date"])
    trading_dates = set(cal["trade_date"])
    return df[df.index.isin(trading_dates)]


def compute_fgi(end_date: Optional[str] = None) -> pd.DataFrame:
    """Compute the Fear & Greed Index.

    Args:
        end_date: Optional cutoff date (YYYY-MM-DD). Defaults to latest.

    Returns:
        DataFrame with columns: date, fgi, sentiment, and 8 sub-scores.
    """
    logger.info("Computing Fear & Greed Index...")

    all_scores = {}

    for name, fn, invert, weight in INDICATORS:
        col_name = name
        logger.info(f"  [{name}] computing...")
        try:
            raw = fn()
            if raw.empty:
                logger.warning(f"  [{name}] EMPTY — skipping")
                continue
            # Find the raw value column (last column)
            raw_col = raw.columns[-1]
            scored = _score_column(raw[raw_col], invert=invert).to_frame(col_name)
            all_scores[col_name] = scored
            logger.info(f"  [{name}] {len(scored)} rows, range [{scored[col_name].min():.1f}, {scored[col_name].max():.1f}]")
        except Exception as e:
            logger.error(f"  [{name}] FAILED: {e}")

    if not all_scores:
        raise RuntimeError("No indicators computed successfully")

    # Merge all scores on date index
    merged = None
    for name, df_score in all_scores.items():
        if merged is None:
            merged = df_score
        else:
            merged = merged.join(df_score, how="outer")

    # Compute FGI = weighted average of available scores
    n_available = merged.notna().sum(axis=1)
    merged["fgi"] = merged.mean(axis=1)  # equal weight among available
    merged["indicators_available"] = n_available.astype(int)

    # Filter to trading days only (use 000300.SH as calendar)
    merged = _filter_trading_days(merged)

    # Require at least 4 indicators for a valid reading
    merged.loc[merged["indicators_available"] < 4, "fgi"] = np.nan

    # Handle edge cases
    merged["fgi"] = merged["fgi"].clip(0, 100)
    merged["sentiment"] = merged["fgi"].apply(_sentiment_label)
    merged["date"] = merged.index
    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")

    # Cutoff
    if end_date:
        merged = merged[merged.index <= pd.Timestamp(end_date)]

    logger.info(
        f"FGI computed: {len(merged)} days, "
        f"range [{merged['fgi'].min():.1f}, {merged['fgi'].max():.1f}], "
        f"latest={merged.iloc[-1]['date']} FGI={merged.iloc[-1]['fgi']:.1f} "
        f"({merged.iloc[-1]['sentiment']})"
    )

    return merged


def latest_fgi() -> dict:
    """Return the latest FGI reading as a dict."""
    df = compute_fgi()
    row = df.iloc[-1]
    return {
        "date": row["date"],
        "fgi": round(float(row["fgi"]), 1),
        "sentiment": row["sentiment"],
        "indicators_available": int(row["indicators_available"]),
        "sub_scores": {
            name: round(float(row[name]), 1) if name in row and not pd.isna(row[name]) else None
            for name, _, _, _ in INDICATORS
        },
    }
