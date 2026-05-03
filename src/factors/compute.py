"""因子批量计算管道

支持:
  1. 表达式因子批量计算 (from registry)
  2. 代码因子计算
  3. 输出 Parquet
"""

from __future__ import annotations

import polars as pl
from pathlib import Path
from typing import Optional

from src.factors.registry import FactorRegistry, Factor
from src.factors.data import load_daily, to_factor_df


def compute_factors(
    factor_names: list[str],
    df: pl.DataFrame | None = None,
    *,
    data_dir: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    ts_codes: list[str] | None = None,
) -> pl.DataFrame:
    """批量计算因子。

    Args:
        factor_names: 因子名列表, e.g. ["ret_5d", "rsi_14", "vol_20d"]
        df: 已加载的 DataFrame (None = 自动从 parquet 加载)
        data_dir: parquet 数据目录
        start_date, end_date: 日期过滤
        ts_codes: 股票过滤

    Returns:
        Polars DataFrame: ts_code, trade_date, factor_1, factor_2, ...
    """
    if df is None:
        df = load_daily(data_dir, start_date, end_date, ts_codes)

    df = to_factor_df(df)

    result = df.select(["ts_code", "trade_date"])

    for name in factor_names:
        factor = FactorRegistry.get(name)
        if factor is None:
            raise ValueError(f"Factor '{name}' not registered")

        values = factor.compute(df)
        if isinstance(values, pl.Series):
            result = result.with_columns(values.alias(name))
        else:
            result = result.with_columns(pl.Series(name, values))

    return result


def export_factors(
    factor_names: list[str],
    output_dir: str | Path,
    *,
    data_dir: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    partition_by: str = "trade_date",
) -> Path:
    """计算因子并导出为 Parquet。

    Args:
        factor_names: 因子名列表
        output_dir: 输出目录
        data_dir: 输入数据目录
        start_date, end_date: 日期范围
        partition_by: 分区字段 (trade_date 或 ts_code)

    Returns:
        输出目录路径。
    """
    df = compute_factors(
        factor_names,
        data_dir=data_dir,
        start_date=start_date,
        end_date=end_date,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    if partition_by == "trade_date":
        for date in df["trade_date"].unique().to_list():
            part = df.filter(pl.col("trade_date") == date)
            date_str = str(date).replace("-", "")
            part.write_parquet(output / f"trade_date={date_str}" / "data.parquet")
    elif partition_by == "ts_code":
        for code in df["ts_code"].unique().to_list():
            part = df.filter(pl.col("ts_code") == code)
            part.write_parquet(output / f"ts_code={code}" / "data.parquet")
    else:
        df.write_parquet(output / "factors.parquet")

    return output
