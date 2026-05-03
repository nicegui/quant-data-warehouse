"""七因子行业轮动 — 策略1落地.

因子（按权重）:
  1. 北向20日净流入 (30%) — raw_moneyflow_hsgt
  2. 分析师EPS增速 (15%) — raw_analyst_forecast (snapshot, 仅当期可用)
  3. 分析师评级强度 (10%) — raw_analyst_forecast
  4. 目标价空间 (5%) — raw_analyst_forecast
  5. 短期反转 (15%) — raw_sw_daily, 5日跌幅最大→得分高
  6. 低波动率 (15%) — raw_sw_daily, 20日 realized vol
  7. 拥挤度 (10%) — raw_sw_daily, 成交额占比+换手率

回测仅用因子1+5+6+7(有历史时间序列)。
全因子排名用于当期推荐。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text
from src.db.session import db_session


# ============================================================
# DATA LOADING
# ============================================================

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


def load_northbound_flow() -> pd.DataFrame:
    """加载北向资金行业流 — 从 raw_moneyflow_hsgt 按行业聚合.

    注: moneyflow_hsgt 是市场级别(沪/深/总), 非行业级别。
    用 stock-level northbound + SW 映射更精确, 但这里用市场流向做近似。
    实际使用时替代为行业级北向(需额外数据)。
    """
    # moneyflow_hsgt is market-level, not sector-level
    # Return empty — we'll use a placeholder approach
    return pd.DataFrame()


def load_analyst_snapshot() -> pd.DataFrame:
    """加载最新分析师一致预期快照, 映射到SW行业."""
    with db_session() as s:
        df = pd.read_sql(
            text("""
                SELECT af.*, ric.index_code as industry_code
                FROM raw_analyst_forecast af
                JOIN ref_index_classify ric
                  ON ric.industry_name = af.industry
                 AND ric.src = 'SW2021'
                 AND ric.level = 'L2'
                WHERE af.snapshot_date = (SELECT MAX(snapshot_date) FROM raw_analyst_forecast)
            """),
            s.bind,
        )
    return df


def load_industry_sw_map() -> pd.DataFrame:
    """SW L2 code → name mapping."""
    with db_session() as s:
        df = pd.read_sql(
            text("""
                SELECT index_code, industry_name
                FROM ref_index_classify
                WHERE src = 'SW2021' AND level = 'L2'
            """),
            s.bind,
        )
    return df


# ============================================================
# FACTOR COMPUTATION
# ============================================================

def compute_momentum_factors(df: pd.DataFrame) -> pd.DataFrame:
    """计算价格类因子: 短期反转(5日), 低波动率(20日), 拥挤度."""
    df = df.sort_values(["ts_code", "trade_date"]).copy()

    # 反转: -5日收益率 (跌得多→得分高)
    df["rev_5d"] = df.groupby("ts_code")["close"].transform(
        lambda x: -x.pct_change(5)
    )

    # 低波: -20日波动率 (波动低→得分高)
    df["vol_20d"] = df.groupby("ts_code")["pct_chg"].transform(
        lambda x: -x.rolling(20).std()
    )

    # 拥挤度
    daily_total = df.groupby("trade_date")["amount"].transform("sum")
    df["amount_share"] = df["amount"] / daily_total
    df["amount_rank"] = df.groupby("trade_date")["amount_share"].rank(pct=True)
    df["turnover_rank"] = df.groupby("trade_date")["vol"].rank(pct=True)
    df["crowding"] = -(df["amount_rank"] + df["turnover_rank"]) / 2  # negative → low crowding scores high

    return df


def compute_analyst_factors(analyst_df: pd.DataFrame) -> pd.DataFrame:
    """计算分析师因子: 评级强度, EPS增速, 目标价空间."""
    af = analyst_df.copy()

    # 评级强度: (买入+增持) / 覆盖数
    af["rating_strength"] = (af["rating_buy_num"].fillna(0) + af["rating_add_num"].fillna(0)) / af[
        "rating_org_num"
    ].clip(lower=1)

    # EPS增速: (EPS2 - EPS1) / abs(EPS1)
    af["eps_growth"] = (af["eps2"] - af["eps1"]) / af["eps1"].abs().clip(lower=0.01)

    # 目标价空间: 简单用 max / min 比值做近似 (无现价的情况下)
    af["target_upside"] = af["aim_price_max"] / af["aim_price_min"].clip(lower=0.01)

    # 聚合到行业
    industry_factors = af.groupby("industry_code").agg(
        rating_strength=("rating_strength", "mean"),
        eps_growth=("eps_growth", "median"),
        target_upside=("target_upside", "median"),
        coverage=("rating_org_num", "sum"),
    ).reset_index()

    return industry_factors


# ============================================================
# SCORING
# ============================================================

def compute_scores(
    df: pd.DataFrame,
    analyst_factors: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute multi-factor scores per industry per date.

    Weights:
      - 北向: 0.30 (placeholder, no sector-level data yet)
      - 反转: 0.20
      - 低波: 0.15
      - 拥挤: 0.10
      - 分析师评级: 0.10
      - 分析师EPS增速: 0.10
      - 目标价空间: 0.05
    """
    df = df.dropna(subset=["rev_5d", "vol_20d", "crowding"]).copy()

    # Z-score normalize within each date (cross-section)
    for col in ["rev_5d", "vol_20d", "crowding"]:
        mean = df.groupby("trade_date")[col].transform("mean")
        std = df.groupby("trade_date")[col].transform("std").clip(lower=1e-8)
        df[f"{col}_z"] = (df[col] - mean) / std

    # Base score from price factors
    df["score"] = (
        0.20 * df["rev_5d_z"]
        + 0.15 * df["vol_20d_z"]
        + 0.10 * df["crowding_z"]
    )

    # Add analyst factors for the latest date
    if analyst_factors is not None and not analyst_factors.empty:
        latest_date = df["trade_date"].max()
        analyst_factors["ts_code"] = analyst_factors["industry_code"]
        # Z-score analyst factors
        for col in ["rating_strength", "eps_growth", "target_upside"]:
            m = analyst_factors[col].mean()
            s = analyst_factors[col].std()
            if s and s > 0:
                analyst_factors[f"{col}_z"] = (analyst_factors[col] - m) / s
            else:
                analyst_factors[f"{col}_z"] = 0

        # Merge to latest date
        latest = df[df["trade_date"] == latest_date].copy()
        latest = latest.merge(
            analyst_factors[["ts_code", "rating_strength_z", "eps_growth_z", "target_upside_z"]],
            on="ts_code",
            how="left",
        )
        # Add analyst component
        latest["analyst_score"] = (
            0.10 * latest["rating_strength_z"].fillna(0)
            + 0.10 * latest["eps_growth_z"].fillna(0)
            + 0.05 * latest["target_upside_z"].fillna(0)
        )
        latest["score"] = latest["score"] + latest["analyst_score"]

        # Update the latest date in main df
        df.loc[df["trade_date"] == latest_date, "score"] = latest["score"].values

    return df


# ============================================================
# BACKTEST
# ============================================================

def backtest_weekly(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """周度横截面排名回测: 买score最高的top_n行业, 持有一周."""
    df = df.copy()
    df["week"] = (
        df["trade_date"].dt.isocalendar().year.astype(str)
        + "-W"
        + df["trade_date"].dt.isocalendar().week.astype(str).str.zfill(2)
    )
    group_col = "week"

    all_periods = sorted(df[group_col].unique())
    results = []

    for i, period in enumerate(all_periods):
        period_df = df[df[group_col] == period]
        if period_df.empty:
            continue

        latest_date = period_df["trade_date"].max()
        last_day = period_df[period_df["trade_date"] == latest_date]
        top = last_day.nlargest(top_n, "score")

        if len(top) < top_n:
            continue

        selected = top["ts_code"].tolist()

        if i + 1 >= len(all_periods):
            break
        next_key = all_periods[i + 1]
        next_df = df[df[group_col] == next_key]
        next_start = next_df["trade_date"].min()
        next_end = next_df["trade_date"].max()

        hold_df = df[
            (df["ts_code"].isin(selected))
            & (df["trade_date"] >= next_start)
            & (df["trade_date"] <= next_end)
        ]
        daily_rets = hold_df.groupby("trade_date")["pct_chg"].mean() / 100
        period_ret = ((1 + daily_rets).prod() - 1) * 100

        results.append({
            "period": period,
            "start_date": latest_date,
            "end_date": next_end,
            "n_sectors": len(selected),
            "period_return": round(period_ret, 2),
            "sectors": ",".join(selected[:3]),
        })

    return pd.DataFrame(results)


# ============================================================
# MAIN
# ============================================================

def run():
    print("=" * 60)
    print("  七因子行业轮动策略")
    print("=" * 60)

    # 1. Load
    print("\n[1/4] 加载数据...")
    df = load_sw_data()
    print(f"  SW日线: {len(df):,} 行")

    analyst_df = load_analyst_snapshot()
    print(f"  分析师快照: {len(analyst_df)} 只票, {analyst_df['industry_code'].nunique()} 个SW行业")

    # 2. Factors
    print("\n[2/4] 计算因子...")
    df = compute_momentum_factors(df)
    analyst_factors = compute_analyst_factors(analyst_df)
    print(f"  分析师行业因子: {len(analyst_factors)} 个行业")
    print(f"  评级强度 均值={analyst_factors['rating_strength'].mean():.2%}")
    print(f"  EPS增速 中位={analyst_factors['eps_growth'].median():.1%}")
    print(f"  覆盖机构 总计={analyst_factors['coverage'].sum():,}")

    # 3. Scores
    print("\n[3/4] 计算得分...")
    df = compute_scores(df, analyst_factors)

    # 4. Latest ranking
    latest = df[df["trade_date"] == df["trade_date"].max()].dropna(subset=["score"])
    print(f"  [debug] latest rows: {len(latest)}, score range: {latest['score'].min():.2f} ~ {latest['score'].max():.2f}")
    top5 = latest.nlargest(5, "score")
    bot5 = latest.nsmallest(5, "score")
    ranked = latest.sort_values("score", ascending=False)

    map_df = load_industry_sw_map()
    name_map = dict(zip(map_df["index_code"], map_df["industry_name"]))

    print(f"\n=== 最新行业排名 ({df['trade_date'].max().date()}) ===\n")
    if len(ranked) == 0:
        print("  (无有效得分数据)")
    else:
        print(f"{'排名':>4}  {'行业':12s}  {'名称':10s}  {'得分':>6}  {'反转':>6}  {'低波':>6}  {'拥挤':>6}")
        print("-" * 65)
        for i, (_, r) in enumerate(ranked.iterrows(), 1):
            code = r.get("ts_code", "?")
            name = name_map.get(code, code)[:10]
            score = r.get("score", float("nan"))
            rev_z = r.get("rev_5d_z", float("nan"))
            vol_z = r.get("vol_20d_z", float("nan"))
            crowd_z = r.get("crowding_z", float("nan"))
            if i <= 5:
                marker = "🔥"
            elif i > len(ranked) - 5:
                marker = "❄️"
            else:
                marker = "  "
            print(
                f"  {marker}{i:>3}  {code:12s}  {name:10s}  "
                f"{score:+6.2f}  {rev_z:+6.2f}  "
                f"{vol_z:+6.2f}  {crowd_z:+6.2f}"
            )

    # 5. Analyst factor detail for top industries
    print(f"\n=== Top 5 行业 — 分析师因子详情 ===")
    top_codes = top5["ts_code"].tolist()
    top_analyst = analyst_factors[analyst_factors["industry_code"].isin(top_codes)]
    for _, r in top_analyst.iterrows():
        name = name_map.get(r["industry_code"], r["industry_code"])[:10]
        print(
            f"  {r['industry_code']:12s} {name:10s}  "
            f"评级强度={r['rating_strength']:.1%}  "
            f"EPS增速={r['eps_growth']:.1%}  "
            f"覆盖={int(r['coverage']):,}家"
        )

    # 6. Backtest (price factors only)
    print(f"\n[4/4] 回测 (价格因子: 反转+低波+拥挤)...")
    bt = backtest_weekly(df, top_n=5)
    if not bt.empty:
        period_rets = bt["period_return"].values / 100
        cum_ret = ((1 + pd.Series(period_rets)).prod() - 1) * 100
        equity = (1 + pd.Series(period_rets)).cumprod()
        peak = equity.cummax()
        mdd = ((equity / peak - 1).min()) * 100
        n = len(bt)
        print(f"  总期数: {n}")
        print(f"  累计收益: {cum_ret:+.1f}%")
        print(f"  年化收益: {(1 + cum_ret/100)**(52/max(n,1)) - 1:+.1%}")
        print(f"  胜率: {(bt['period_return'] > 0).mean():.1%}")
        print(f"  最大回撤: {mdd:+.1f}%")

    print("\n" + "=" * 60)
    print("  完成")
    print("=" * 60)

    return df


if __name__ == "__main__":
    run()
