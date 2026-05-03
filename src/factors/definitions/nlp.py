"""NLP/情绪因子 — 从 LLM 标注结果读取

需要先运行 annotator.py 生成标注 parquet，然后这些因子可以
像普通因子一样参与 compute_factors()。

标注输出列:
  datetime, ts_code, pub_date, sentiment, event_type, impact, summary, keywords
"""

from __future__ import annotations

import json
import polars as pl
from pathlib import Path
from src.factors.registry import register_factor


DEFAULT_ANNOTATION_DIR = Path("data/annotations/annotations.parquet")


def _load_annotations(path: str | Path | None = None) -> pl.DataFrame:
    """加载 LLM 标注结果。"""
    p = Path(path or DEFAULT_ANNOTATION_DIR)
    if not p.exists():
        raise FileNotFoundError(f"Annotations not found at {p}. Run NewsAnnotator first.")
    return pl.read_parquet(p)


# ═══════════════════════════════════════════
# 情绪因子
# ═══════════════════════════════════════════

@register_factor("sentiment", "news_sentiment", impl="code")
def news_sentiment(df: pl.DataFrame) -> pl.Series:
    """新闻日均情绪 (per stock, per day)。

    从标注结果聚合: 当日该股票所有新闻 sentiment 均值。
    """
    ann = _load_annotations()
    # Aggregate: per ts_code per pub_date, average sentiment
    daily = (
        ann.filter(pl.col("ts_code") != "")
        .group_by(["ts_code", "pub_date"])
        .agg([
            pl.col("sentiment").mean().alias("avg_sentiment"),
            pl.col("sentiment").count().alias("news_count"),
        ])
    )

    # Merge onto the factor DataFrame
    return (
        df.select(["ts_code", "trade_date"])
        .join(
            daily,
            left_on=["ts_code", "trade_date"],
            right_on=["ts_code", "pub_date"],
            how="left",
        )
        .get_column("avg_sentiment")
    )


@register_factor("sentiment", "news_count", impl="code")
def news_count(df: pl.DataFrame) -> pl.Series:
    """新闻数量 (per stock, per day)。"""
    ann = _load_annotations()
    daily = (
        ann.filter(pl.col("ts_code") != "")
        .group_by(["ts_code", "pub_date"])
        .agg(pl.col("sentiment").count().alias("n"))
    )
    return (
        df.select(["ts_code", "trade_date"])
        .join(
            daily,
            left_on=["ts_code", "trade_date"],
            right_on=["ts_code", "pub_date"],
            how="left",
        )
        .get_column("n")
    )


@register_factor("sentiment", "news_sentiment_5d", impl="code")
def news_sentiment_5d(df: pl.DataFrame) -> pl.Series:
    """5日累计新闻情绪。
    
    聚合近5日新闻的平均 sentiment，加权每条新闻的 impact。
    """
    ann = _load_annotations()
    # Weighted by impact: sentiment * impact / sum(impact)
    daily = (
        ann.filter(pl.col("ts_code") != "")
        .group_by(["ts_code", "pub_date"])
        .agg([
            (pl.col("sentiment") * pl.col("impact")).sum().alias("weighted_sum"),
            pl.col("impact").sum().alias("total_impact"),
        ])
        .with_columns(
            (pl.col("weighted_sum") / pl.col("total_impact")).alias("weighted_sentiment")
        )
    )

    # Join then rolling mean
    merged = df.select(["ts_code", "trade_date"]).join(
        daily,
        left_on=["ts_code", "trade_date"],
        right_on=["ts_code", "pub_date"],
        how="left",
    ).with_columns(pl.col("weighted_sentiment").fill_null(0))

    return merged.with_columns(
        pl.col("weighted_sentiment")
        .rolling_mean(window_size=5, min_periods=1)
        .over("ts_code")
        .alias("sentiment_5d")
    )["sentiment_5d"]


# ═══════════════════════════════════════════
# 事件分类因子
# ═══════════════════════════════════════════

@register_factor("sentiment", "news_earnings_flag", impl="code")
def news_earnings_flag(df: pl.DataFrame) -> pl.Series:
    """是否有业绩相关新闻 (当日)。0/1。"""
    ann = _load_annotations()
    earnings = (
        ann.filter((pl.col("ts_code") != "") & (pl.col("event_type") == "earnings"))
        .select(["ts_code", "pub_date"])
        .unique()
        .with_columns(pl.lit(1).alias("has_earnings"))
    )
    return (
        df.select(["ts_code", "trade_date"])
        .join(
            earnings,
            left_on=["ts_code", "trade_date"],
            right_on=["ts_code", "pub_date"],
            how="left",
        )
        .get_column("has_earnings")
        .fill_null(0)
    )


@register_factor("sentiment", "news_merger_flag", impl="code")
def news_merger_flag(df: pl.DataFrame) -> pl.Series:
    """是否有并购相关新闻。0/1。"""
    ann = _load_annotations()
    merger = (
        ann.filter((pl.col("ts_code") != "") & (pl.col("event_type") == "merger"))
        .select(["ts_code", "pub_date"])
        .unique()
        .with_columns(pl.lit(1).alias("has_merger"))
    )
    return (
        df.select(["ts_code", "trade_date"])
        .join(
            merger,
            left_on=["ts_code", "trade_date"],
            right_on=["ts_code", "pub_date"],
            how="left",
        )
        .get_column("has_merger")
        .fill_null(0)
    )
