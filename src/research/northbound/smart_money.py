"""北向资金 Smart Money 因子研究.

分析维度:
  1. 日频净买入 vs 未来收益 IC
  2. 北向 + 融资 + 主力三路资金共振
  3. 北向行为的择时/择股信号
"""

import logging
import numpy as np
import pandas as pd
from sqlalchemy import text
from src.db.session import db_session

logger = logging.getLogger(__name__)


def load_data() -> pd.DataFrame:
    """加载北向 + 000300 + 融资 + 成交额 日频数据."""
    with db_session() as s:
        # 北向资金
        nb = pd.read_sql(
            text("SELECT trade_date, north_money FROM raw_moneyflow_hsgt ORDER BY trade_date"),
            s.bind,
        )
        # 沪深300
        idx = pd.read_sql(
            text("SELECT trade_date, close FROM raw_index_daily WHERE ts_code='000300.SH' ORDER BY trade_date"),
            s.bind,
        )
        # 融资买入
        margin = pd.read_sql(
            text("SELECT trade_date, SUM(rzmre) as margin_buy FROM raw_margin_detail GROUP BY trade_date ORDER BY trade_date"),
            s.bind,
        )
        # 全市场成交额
        amt = pd.read_sql(
            text("SELECT trade_date, SUM(amount) as total_amount FROM raw_daily_info WHERE exchange IN ('SH','SZ') GROUP BY trade_date ORDER BY trade_date"),
            s.bind,
        )

    for df in [nb, idx, margin, amt]:
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df.set_index("trade_date", inplace=True)

    # Merge
    merged = nb.join(idx, how="inner").join(margin, how="inner").join(amt, how="inner")
    merged = merged.sort_index()

    # 日频净买入
    merged["net_north"] = merged["north_money"].diff()
    merged["net_north_pct"] = merged["net_north"] / merged["total_amount"] * 100

    # 未来收益
    for horizon in [1, 5, 10, 20]:
        merged[f"fwd_ret_{horizon}d"] = merged["close"].pct_change(horizon).shift(-horizon)
        merged[f"fwd_ret_{horizon}d_pct"] = merged[f"fwd_ret_{horizon}d"] * 100

    # 融资买入占比
    merged["margin_pct"] = merged["margin_buy"] / merged["total_amount"] * 100

    # 北向连续流入天数
    merged["nb_direction"] = (merged["net_north"] > 0).astype(int)
    merged["nb_streak"] = merged["nb_direction"].groupby(
        (merged["nb_direction"] != merged["nb_direction"].shift()).cumsum()
    ).cumcount() + 1
    merged.loc[merged["nb_direction"] == 0, "nb_streak"] = (
        -merged.loc[merged["nb_direction"] == 0, "nb_streak"]
    )

    return merged


def ic_analysis(df: pd.DataFrame) -> dict:
    """北向净买入 vs 未来收益 IC 分析."""
    results = {}
    for horizon in [1, 5, 10, 20]:
        col = f"fwd_ret_{horizon}d"
        valid = df[["net_north_pct", col]].dropna()
        ic = valid["net_north_pct"].corr(valid[col])  # Pearson
        # 滚动 IC
        roll_ic = valid["net_north_pct"].rolling(60).corr(valid[col])
        results[horizon] = {
            "ic": round(ic, 4),
            "ic_ir": round(roll_ic.mean() / roll_ic.std(), 2) if roll_ic.std() > 0 else 0,
            "ic_pos_ratio": round((roll_ic > 0).mean(), 3),
        }
    return results


def streak_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """连续流入/流出天数 → 未来收益."""
    bins = [-99, -10, -5, -3, -1, 1, 3, 5, 10, 99]
    labels = ["流出10+", "流出5-10", "流出3-5", "流出1-2", "单日", "流入1-2", "流入3-5", "流入5-10", "流入10+"]
    df["streak_bin"] = pd.cut(df["nb_streak"], bins=bins, labels=labels, right=False)

    results = []
    for horizon in [5, 10, 20]:
        g = df.groupby("streak_bin")[f"fwd_ret_{horizon}d_pct"].agg(["mean", "std", "count"])
        g["ann"] = g["mean"] * (252 / horizon)
        g["ir"] = g["mean"] / g["std"] * np.sqrt(252 / horizon)
        g.columns = [f"{c}_{horizon}d" for c in g.columns]
        results.append(g)
    return pd.concat(results, axis=1)


def resonance_signal(df: pd.DataFrame) -> pd.DataFrame:
    """三路资金共振：北向 + 融资 + 成交额增量."""
    # 北向信号: 净买入占成交额比 Z-score
    df["nb_z"] = (df["net_north_pct"] - df["net_north_pct"].rolling(60).mean()) / df["net_north_pct"].rolling(60).std()
    # 融资信号
    df["margin_chg"] = df["margin_pct"].diff()
    df["margin_z"] = (df["margin_chg"] - df["margin_chg"].rolling(60).mean()) / df["margin_chg"].rolling(60).std()
    # 成交额信号
    df["amount_chg"] = df["total_amount"].pct_change()
    df["amount_z"] = (df["amount_chg"] - df["amount_chg"].rolling(60).mean()) / df["amount_chg"].rolling(60).std()

    # 共振: 三者同向 = 强信号
    df["resonance_bull"] = ((df["nb_z"] > 1) & (df["margin_z"] > 1) & (df["amount_z"] > 1)).astype(int)
    df["resonance_bear"] = ((df["nb_z"] < -1) & (df["margin_z"] < -1) & (df["amount_z"] < -1)).astype(int)

    return df


def run():
    """主分析."""
    logger.info("加载数据...")
    df = load_data()

    # 1. IC 分析
    logger.info("IC 分析...")
    ic = ic_analysis(df)
    print("\n=== 北向净买入 IC ===")
    print(f"{'Horizon':>8} {'IC':>8} {'IC_IR':>8} {'IC>0%':>8}")
    for h, r in ic.items():
        print(f"{h:>4}d   {r['ic']:>8.4f} {r['ic_ir']:>8.2f} {r['ic_pos_ratio']:>7.1%}")

    # 2. 连续流入分析
    logger.info("连续流入分析...")
    streak = streak_analysis(df)
    print("\n=== 连续流入/流出 → 未来收益 ===")
    cols = [c for c in streak.columns if "mean" in c]
    print(streak[cols].round(2).to_string())

    # 3. 三路共振
    logger.info("三路共振...")
    df = resonance_signal(df)
    for name, col in [("看多共振", "resonance_bull"), ("看空共振", "resonance_bear")]:
        mask = df[col] == 1
        n = mask.sum()
        if n > 0:
            avg5 = df.loc[mask, "fwd_ret_5d_pct"].mean()
            avg20 = df.loc[mask, "fwd_ret_20d_pct"].mean()
            print(f"\n{name} ({n}次): 5日 {avg5:+.2f}%  20日 {avg20:+.2f}%")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    run()
