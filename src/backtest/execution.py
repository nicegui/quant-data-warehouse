"""执行模拟器 — 交易成本模型

业界标准实现:
  - Almgren-Chriss 平方根冲击模型 (2005, J. Risk)
  - Barra 风格永久+临时冲击分解
  - 滑点模型 (bid-ask spread)
  - 佣金 (万3 默认)

参考:
  Almgren, R. and Chriss, N. (2000). "Optimal Execution of Portfolio Transactions"
  Kissell, R. (2013). "The Science of Algorithmic Trading and Portfolio Management"
"""

from __future__ import annotations

import polars as pl
from dataclasses import dataclass


@dataclass
class CostModel:
    """Almgren-Chriss 交易成本模型参数。

    Total cost = permanent_impact + temporary_impact + spread + commission

    permanent_impact = sigma * sign(Q) * (|Q| / ADV) ^ 0.5
    temporary_impact = eta * sigma * (|Q| / (ADV * tau)) ^ 0.6
    spread = 0.5 * bid_ask_spread
    """

    sigma: float = 0.02       # 日波动率 (annualized 32% ~ daily 2%)
    eta: float = 0.142        # 临时冲击系数 (Kissell calibration)
    gamma: float = 2.5e-6     # 永久冲击系数
    bid_ask_spread: float = 0.001  # 买卖价差 (10bp)
    commission_rate: float = 0.0003  # 佣金率 (万3)
    min_commission: float = 5.0      # 最低佣金 (元)

    def total_cost(
        self,
        trade_value: float,         # 交易金额
        daily_volume: float,        # 日均成交额
        is_buy: bool = True,
    ) -> float:
        """计算单笔交易总成本。

        Args:
            trade_value: 交易的金额 (元)
            daily_volume: 该股票日均成交额 (元)
            is_buy: 买入=True, 卖出=False

        Returns:
            总成本占交易金额的比例 (0~1)
        """
        if daily_volume <= 0 or trade_value <= 0:
            return self.commission_rate * 2  # fallback

        participation = trade_value / daily_volume  # 参与率
        sign = 1.0 if is_buy else -1.0

        # Permanent impact (information leakage)
        permanent = self.gamma * self.sigma * abs(participation) ** 0.5

        # Temporary impact (liquidity demand)
        temporary = self.eta * self.sigma * participation ** 0.6

        # Spread cost
        spread_cost = 0.5 * self.bid_ask_spread

        # Commission
        commission = max(trade_value * self.commission_rate, self.min_commission) / trade_value

        return permanent + temporary + spread_cost + commission


# ═══════════════════════════════════════════
# 组合级成交模拟
# ═══════════════════════════════════════════

def simulate_execution(
    target_weights: pl.DataFrame,      # ts_code, target_weight
    current_weights: pl.DataFrame,     # ts_code, current_weight (None = all cash)
    prices: pl.DataFrame,              # ts_code, close, daily_volume (or adv)
    capital: float,
    cost_model: CostModel | None = None,
) -> tuple[pl.DataFrame, dict]:
    """模拟一次调仓执行，计算实际成本。

    Args:
        target_weights: 目标权重
        current_weights: 当前权重 (None = 全部现金)
        prices: 当前价格 + 日均成交额
        capital: 总资金
        cost_model: 成本模型

    Returns:
        (executed trades, cost summary)
    """
    cm = cost_model or CostModel()

    merged = (
        target_weights
        .join(current_weights, on="ts_code", how="outer")
        .join(prices, on="ts_code", how="left")
    )

    merged = merged.fill_null(0.0)
    merged = merged.with_columns([
        (pl.col("target_weight") - pl.col("current_weight")).alias("delta_weight"),
        ((pl.col("target_weight") - pl.col("current_weight")) * capital).alias("trade_value"),
    ])

    # Compute cost per stock
    trades_list = []
    total_cost = 0.0
    total_turnover = 0.0

    for row in merged.iter_rows(named=True):
        tv = abs(row["trade_value"])
        if tv < 100:  # skip negligible
            continue

        is_buy = row["trade_value"] > 0
        dv = row.get("daily_volume", tv * 10)  # fallback

        cost_pct = cm.total_cost(tv, dv, is_buy)
        cost_amt = tv * cost_pct
        total_cost += cost_amt
        total_turnover += tv

        trades_list.append({
            "ts_code": row["ts_code"],
            "target_weight": row["target_weight"],
            "delta_weight": row["delta_weight"],
            "trade_value": row["trade_value"],
            "cost_pct": cost_pct,
            "cost_amt": cost_amt,
        })

    return (
        pl.DataFrame(trades_list) if trades_list else pl.DataFrame(),
        {
            "total_turnover": total_turnover,
            "total_cost": total_cost,
            "cost_bps": (total_cost / total_turnover * 10000) if total_turnover > 0 else 0,
            "turnover_pct": total_turnover / capital * 100 if capital > 0 else 0,
        },
    )
