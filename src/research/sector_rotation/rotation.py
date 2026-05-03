"""行业轮动模型.

分析维度:
  1. 申万行业动量排序 → 周度调仓模拟
  2. 行业拥挤度（成交额占比 + 换手率分位）
  3. 动量 + 拥挤度 双因子选行业
"""

import logging
import numpy as np
import pandas as pd
from sqlalchemy import text
from src.db.session import db_session

logger = logging.getLogger(__name__)


def load_sw_data() -> pd.DataFrame:
    """加载申万行业日线数据."""
    with db_session() as s:
        df = pd.read_sql(
            text("""
                SELECT trade_date, ts_code, close, pct_change as pct_chg, vol, amount
                FROM raw_sw_daily
                ORDER BY trade_date, ts_code
            """),
            s.bind,
        )
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df


def compute_momentum(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """计算行业动量（过去 N 日收益率）."""
    df = df.sort_values(["ts_code", "trade_date"])
    df["momentum"] = df.groupby("ts_code")["close"].transform(
        lambda x: x.pct_change(lookback)
    )
    return df


def compute_crowding(df: pd.DataFrame) -> pd.DataFrame:
    """计算行业拥挤度.

    拥挤度 = 0.5 * 成交额占比分位 + 0.5 * 换手率分位
    """
    df = df.copy()
    df = df.sort_values(["trade_date", "ts_code"])

    # 每日总成交额
    daily_total = df.groupby("trade_date")["amount"].transform("sum")
    df["amount_share"] = df["amount"] / daily_total

    # 换手率（用 amount/close 近似，或用已有 vol）
    # raw_sw_daily 没有 turnover_ratio，用 vol 替代
    df["imp_turnover"] = df["vol"]

    # 横截面分位
    df["amount_rank"] = df.groupby("trade_date")["amount_share"].rank(pct=True)
    df["turnover_rank"] = df.groupby("trade_date")["imp_turnover"].rank(pct=True)
    df["crowding"] = (df["amount_rank"] + df["turnover_rank"]) / 2

    return df


def rotation_backtest(df: pd.DataFrame, top_n: int = 5, rebalance_freq: str = "W") -> pd.DataFrame:
    """行业轮动回测.

    策略: 选取动量最强的 top_n 个行业，等权持有，周度调仓.
    """
    df = df.copy()
    df = df.sort_values(["trade_date", "ts_code"])

    # 按调仓频率分组
    if rebalance_freq == "W":
        df["week"] = df["trade_date"].dt.isocalendar().year.astype(str) + "-W" + df["trade_date"].dt.isocalendar().week.astype(str).str.zfill(2)
        group_col = "week"
    else:
        df["month"] = df["trade_date"].dt.to_period("M")
        group_col = "month"

    # 每期选 top_n
    # Pre-sort unique periods to find the immediate next period
    all_periods = sorted(df[group_col].unique())
    results = []
    for i, period in enumerate(all_periods):
        period_df = df[df[group_col] == period]
        latest_date = period_df["trade_date"].max()
        # 取该期最后一天的动量
        last_day = period_df[period_df["trade_date"] == latest_date]
        top = last_day.nlargest(top_n, "momentum")

        if len(top) < top_n:
            continue

        selected = top["ts_code"].tolist()

        # 紧邻下一期的收益
        if i + 1 >= len(all_periods):
            break
        next_period_key = all_periods[i + 1]
        next_period_df = df[df[group_col] == next_period_key]
        next_start = next_period_df["trade_date"].min()
        next_end = next_period_df["trade_date"].max()

        # 等权组合
        next_df = df[(df["ts_code"].isin(selected)) & (df["trade_date"] >= next_start) & (df["trade_date"] <= next_end)]
        daily_rets = next_df.groupby("trade_date")["pct_chg"].mean() / 100
        period_ret = ((1 + daily_rets).prod() - 1) * 100  # compound daily returns

        results.append({
            "period": period,
            "start_date": latest_date,
            "end_date": next_end,
            "n_sectors": len(selected),
            "period_return": round(period_ret, 2),
            "sectors": ",".join(selected[:3]),
        })

    return pd.DataFrame(results)


def sector_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """行业间相关性矩阵（最近 252 天）."""
    recent = df[df["trade_date"] >= df["trade_date"].max() - pd.Timedelta(days=365)]
    pivot = recent.pivot(index="trade_date", columns="ts_code", values="pct_chg")
    corr = pivot.corr()
    return corr


def run():
    """主分析."""
    logger.info("加载申万行业数据...")
    df = load_sw_data()
    df = compute_momentum(df, lookback=20)
    df = compute_crowding(df)

    # 1. 动量最强/最弱行业
    latest = df[df["trade_date"] == df["trade_date"].max()].dropna(subset=["momentum"])
    print(f"\n=== 最新行业动量 ({df['trade_date'].max().date()}) ===")
    top5 = latest.nlargest(5, "momentum")[["ts_code", "momentum", "crowding"]]
    bot5 = latest.nsmallest(5, "momentum")[["ts_code", "momentum", "crowding"]]
    print("Top 5:")
    for _, r in top5.iterrows():
        print(f"  {r['ts_code']:20s}  动量={r['momentum']:+.2%}  拥挤度={r['crowding']:.2f}")
    print("Bottom 5:")
    for _, r in bot5.iterrows():
        print(f"  {r['ts_code']:20s}  动量={r['momentum']:+.2%}  拥挤度={r['crowding']:.2f}")

    # 2. 动量 + 拥挤度 双因子选行业（动量大 + 拥挤度低 = 最优）
    latest["score"] = latest["momentum"].rank(pct=True) + (1 - latest["crowding"])
    best = latest.nlargest(5, "score")[["ts_code", "momentum", "crowding", "score"]]
    print(f"\n=== 双因子精选（动量↑ + 拥挤↓） ===")
    for _, r in best.iterrows():
        print(f"  {r['ts_code']:20s}  动量={r['momentum']:+.2%}  拥挤={r['crowding']:.2f}  得分={r['score']:.2f}")

    # 3. 轮动回测
    logger.info("行业轮动回测...")
    bt = rotation_backtest(df, top_n=5, rebalance_freq="W")
    if not bt.empty:
        period_rets = bt["period_return"].values / 100
        cum_ret = ((1 + period_rets).prod() - 1) * 100
        # cumulative equity curve for max drawdown
        equity = (1 + pd.Series(period_rets)).cumprod()
        peak = equity.cummax()
        mdd = ((equity / peak - 1).min()) * 100
        n_periods = len(bt)
        print(f"\n=== 周度动量轮动回测 === ")
        print(f"  总期数: {n_periods}")
        print(f"  累计收益: {cum_ret:+.1f}%")
        print(f"  年化收益: {(1 + cum_ret/100)**(52/n_periods) - 1:+.1%}")
        print(f"  胜率: {(bt['period_return'] > 0).mean():.1%}")
        print(f"  最大回撤: {mdd:+.1f}%")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    run()
