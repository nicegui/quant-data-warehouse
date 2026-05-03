"""数据适配层 — Parquet/DuckDB → Polars DataFrame

从 curated parquet 层读取数据，组装为因子计算所需的 DataFrame。

数据源:
  - curated/stock_daily_adj/  → 复权后的 OHLCV
  - ref/adj_factor/           → 复权因子
  - ref/stock_basic/          → 股票基础信息

输出: Polars DataFrame with columns:
  ts_code, trade_date, open, high, low, close, volume, amount, ...
  (按 ts_code 分组, trade_date 排序)
"""

from __future__ import annotations

import polars as pl
from pathlib import Path


# 默认数据路径
DEFAULT_DATA_DIR = Path("data/parquet")


def load_daily(
    data_dir: str | Path | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    ts_codes: list[str] | None = None,
) -> pl.DataFrame:
    """加载日频行情数据。

    Args:
        data_dir: parquet 文件根目录
        start_date: 起始日期 YYYYMMDD
        end_date: 截止日期 YYYYMMDD
        ts_codes: 股票代码过滤 (None = 全部)

    Returns:
        Polars DataFrame, columns: ts_code, trade_date, open, high, low,
        close, volume, amount, turnover_rate, adj_factor, pre_close
    """
    path = Path(data_dir or DEFAULT_DATA_DIR) / "curated/stock_daily_adj"

    if not path.exists():
        raise FileNotFoundError(
            f"Data not found at {path}. Run parquet export first."
        )

    df = pl.read_parquet(str(path) + "/*.parquet")

    if start_date:
        df = df.filter(pl.col("trade_date") >= start_date)
    if end_date:
        df = df.filter(pl.col("trade_date") <= end_date)
    if ts_codes:
        df = df.filter(pl.col("ts_code").is_in(ts_codes))

    return df.sort(["ts_code", "trade_date"])


def load_financial(
    data_dir: str | Path | None = None,
    report_dates: list[str] | None = None,
) -> pl.DataFrame:
    """加载财务数据 (用于估值/质量因子)。

    Returns columns: ts_code, end_date, roe, roa, gross_margin,
                     net_margin, debt_ratio, eps, bvps, ...
    """
    path = Path(data_dir or DEFAULT_DATA_DIR) / "curated/financial_reports"
    if not path.exists():
        raise FileNotFoundError(f"Financial data not found at {path}")

    df = pl.read_parquet(str(path) + "/*.parquet")

    if report_dates:
        df = df.filter(pl.col("end_date").is_in(report_dates))

    return df.sort(["ts_code", "end_date"])


def load_moneyflow(
    data_dir: str | Path | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pl.DataFrame:
    """加载资金流数据 (用于情绪因子)。"""
    path = Path(data_dir or DEFAULT_DATA_DIR) / "raw/moneyflow"
    if not path.exists():
        raise FileNotFoundError(f"Moneyflow data not found at {path}")

    df = pl.read_parquet(str(path) + "/*.parquet")

    if start_date:
        df = df.filter(pl.col("trade_date") >= start_date)
    if end_date:
        df = df.filter(pl.col("trade_date") <= end_date)

    return df.sort(["ts_code", "trade_date"])


def to_factor_df(
    df: pl.DataFrame,
    extra_cols: list[str] | None = None,
) -> pl.DataFrame:
    """准备因子计算 DataFrame — 确保必需列存在，添加计算字段。

    必需列: ts_code, trade_date, open, high, low, close, volume
    可选: amount, adj_factor, turnover_rate

    计算字段:
      - vwap = amount / volume (如果 amount 存在)
      - pct_chg = close / close.shift(1) - 1
    """
    required = {"ts_code", "trade_date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result = df.clone()

    # vwap
    if "amount" in result.columns:
        result = result.with_columns(
            (pl.col("amount") / pl.col("volume")).alias("vwap")
        )

    # pct_chg (per stock)
    result = result.sort(["ts_code", "trade_date"])
    result = result.with_columns(
        (pl.col("close") / pl.col("close").shift(1).over("ts_code") - 1.0).alias(
            "pct_chg"
        )
    )

    # pre_close
    if "pre_close" not in result.columns:
        result = result.with_columns(
            pl.col("close").shift(1).over("ts_code").alias("pre_close")
        )

    return result
