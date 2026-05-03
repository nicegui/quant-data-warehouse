"""涨跌停统计套利研究 — 细腻版.

分析维度:
  1. 首板/连板/炸板 → 次日溢价（去重+超额收益）
  2. 封板时间效应（早封 vs 晚封）
  3. 行业涨停联动 → 板块动量
"""

import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import text
from src.db.session import db_session

logger = logging.getLogger(__name__)


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """加载涨跌停 + 个股日线 + 指数."""
    with db_session() as s:
        limit = pd.read_sql(
            text("""
                SELECT trade_date, ts_code, industry, name, close, pct_chg,
                       amount, turnover_ratio, first_time, last_time, open_times, lim
                FROM raw_limit_list_d
                ORDER BY trade_date, ts_code
            """),
            s.bind,
        )
        # 个股日线 — 用 stk_factor_pro（947万行，覆盖全A）
        stk = pd.read_sql(
            text("""
                SELECT trade_date, ts_code, close
                FROM raw_stk_factor_pro
                ORDER BY trade_date, ts_code
            """),
            s.bind,
        )
        # 市场收益 — 000300
        idx = pd.read_sql(
            text("""
                SELECT trade_date, close
                FROM raw_index_daily
                WHERE ts_code = '000300.SH'
                ORDER BY trade_date
            """),
            s.bind,
        )

    limit["trade_date"] = pd.to_datetime(limit["trade_date"])
    stk["trade_date"] = pd.to_datetime(stk["trade_date"])

    # 个股次日收益率
    stk = stk.sort_values(["ts_code", "trade_date"])
    stk["next_ret"] = stk.groupby("ts_code")["close"].shift(-1) / stk["close"] - 1

    # 市场次日收益
    idx["trade_date"] = pd.to_datetime(idx["trade_date"])
    idx = idx.set_index("trade_date").sort_index()
    idx["next_ret"] = idx["close"].shift(-1) / idx["close"] - 1
    idx = idx[["next_ret"]].rename(columns={"next_ret": "mkt_ret"})

    return limit, stk, idx


def parse_first_time(t: str) -> Optional[float]:
    """HHMMSS → 距开盘分钟数. '93749' (09:37:49) → 7.8min."""
    if pd.isna(t) or not t:
        return None
    t = str(int(t)).strip().zfill(6)
    try:
        h, m, s = int(t[:2]), int(t[2:4]), int(t[4:6])
        minutes_from_midnight = h * 60 + m + s / 60
        # Market opens at 09:30 = 570 minutes from midnight
        return minutes_from_midnight - 570
    except (ValueError, IndexError):
        return None


def classify_boards(df: pd.DataFrame) -> pd.DataFrame:
    """涨停分类：自己算连板（连续涨停天数）."""
    df = df.copy()

    # 解析封板时间
    df["first_min"] = df["first_time"].apply(parse_first_time)

    # 按股票日期排序，标记连续涨停
    z_only = df[df["lim"] == "Z"].sort_values(["ts_code", "trade_date"])
    z_only["prev_date"] = z_only.groupby("ts_code")["trade_date"].shift(1)
    z_only["is_consecutive"] = (z_only["trade_date"] - z_only["prev_date"]).dt.days == 1

    # 连板计数
    z_only["streak_id"] = (~z_only["is_consecutive"]).cumsum()
    z_only["board_count"] = z_only.groupby(["ts_code", "streak_id"]).cumcount() + 1

    # 合并回原 df
    board_map = z_only.set_index(["ts_code", "trade_date"])["board_count"]
    df = df.join(board_map, on=["ts_code", "trade_date"])

    # 分类
    df["board_type"] = "其他"
    df.loc[df["lim"] == "Z", "board_type"] = "首板"
    df.loc[(df["lim"] == "Z") & (df["board_count"] > 1), "board_type"] = "连板"
    df.loc[df["lim"] == "U", "board_type"] = "炸板"

    return df


def next_day_analysis(df: pd.DataFrame, stk: pd.DataFrame, idx: pd.DataFrame) -> dict:
    """涨停次日超额收益分析."""
    # 合并次日个股收益
    nd = stk[["ts_code", "trade_date", "next_ret"]].copy()
    df = df.merge(nd, on=["ts_code", "trade_date"], how="left")
    # 合并市场收益
    df = df.join(idx, on="trade_date", how="left")
    df["excess_ret"] = df["next_ret"] - df["mkt_ret"]

    results = {}
    for btype in ["首板", "连板", "炸板"]:
        sub = df[df["board_type"] == btype].dropna(subset=["next_ret"])
        if len(sub) < 10:
            continue
        results[btype] = {
            "count": len(sub),
            "win_rate": round((sub["next_ret"] > 0).mean(), 3),
            "avg_ret": round(sub["next_ret"].mean() * 100, 2),
            "avg_excess": round(sub["excess_ret"].mean() * 100, 2),
            "median_ret": round(sub["next_ret"].median() * 100, 2),
            "avg_amount": round(sub["amount"].mean() / 1e8, 1),
            "avg_turnover": round(sub["turnover_ratio"].mean(), 1),
        }
    return results


def time_effect(df: pd.DataFrame) -> pd.DataFrame:
    """封板时间效应：早封 vs 晚封."""
    z = df[df["lim"] == "Z"].dropna(subset=["first_min"])
    if len(z) < 100:
        return pd.DataFrame()

    # 按时间段分桶（距开盘分钟数）
    # 09:30~09:45=0-15, 09:45~10:00=15-30, 10:00~10:30=30-60,
    # 10:30~11:30=60-120, 13:00~14:30=120-210, 14:30~15:00=210-240
    bins = [0, 15, 30, 60, 120, 210, 240, 999]
    labels = ["09:30-45", "09:45-10", "10-10:30", "10:30-11:30", "13-14:30", "14:30-15", "尾盘>15:00"]
    z["time_bin"] = pd.cut(z["first_min"], bins=bins, labels=labels, right=False)

    g = z.groupby("time_bin", observed=False).agg(
        数量=("ts_code", "count"),
        均涨幅=("pct_chg", "mean"),
        均成交额=("amount", lambda x: x.mean() / 1e8),
    ).round(2)
    return g


def sector_contagion(df: pd.DataFrame) -> pd.DataFrame:
    """行业涨停联动：同行业涨停数 → 板块动向."""
    z = df[df["lim"] == "Z"].dropna(subset=["industry"])
    z = z[z["industry"] != ""]

    # 每日每行业涨停数
    daily = z.groupby(["trade_date", "industry"]).size().reset_index(name="z_count")

    # 涨停数分布
    dist = daily.groupby("z_count").agg(
        天数=("trade_date", "count"),
    ).sort_index()

    # 行业涨停热度 Top
    hot = z.groupby("industry").size().sort_values(ascending=False).head(10)

    return dist, hot


def run():
    """主分析."""
    logger.info("加载数据...")
    limit, stk, idx = load_data()
    limit = classify_boards(limit)

    # 1. 分类统计
    print(f"\n{'='*55}")
    print(f"  涨跌停统计")
    print(f"{'='*55}")
    board_stats = limit["board_type"].value_counts()
    for k, v in board_stats.items():
        print(f"  {k:6s}: {v:>8,}")

    # 2. 次日溢价
    print(f"\n{'='*55}")
    print(f"  次日超额收益")
    print(f"{'='*55}")
    nd = next_day_analysis(limit, stk, idx)
    for btype, s in nd.items():
        print(f"\n  [{btype}] n={s['count']:,}")
        print(f"    胜率: {s['win_rate']:.1%}  均收益: {s['avg_ret']:+.2f}%  超额: {s['avg_excess']:+.2f}%")
        print(f"    中位收益: {s['median_ret']:+.2f}%  均成交额: {s['avg_amount']:.1f}亿  均换手: {s['avg_turnover']:.1f}%")

    # 3. 封板时间
    print(f"\n{'='*55}")
    print(f"  封板时间效应")
    print(f"{'='*55}")
    te = time_effect(limit)
    if not te.empty:
        for idx_row, row in te.iterrows():
            bar = "█" * max(1, int(row["数量"] / te["数量"].max() * 30))
            print(f"  {idx_row:8s}  {row['数量']:>5,}只  均涨幅{row['均涨幅']:+.1f}%  均额{row['均成交额']:.1f}亿  {bar}")

    # 4. 行业联动
    print(f"\n{'='*55}")
    print(f"  行业涨停联动")
    print(f"{'='*55}")
    dist, hot = sector_contagion(limit)
    print(f"\n  涨停数分布:")
    for cnt, row in dist.head(10).iterrows():
        print(f"    {cnt:2d}只同时涨停: {int(row['天数']):>5}天")
    print(f"\n  行业涨停热度 Top 10:")
    for ind, cnt in hot.items():
        print(f"    {ind:10s} {cnt:>5,}次")

    return limit


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    run()
