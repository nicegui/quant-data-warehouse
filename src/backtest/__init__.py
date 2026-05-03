"""回测框架 — 向量化引擎 + 事件驱动 + 业绩归因

架构:
  core.py         — VectorizedEngine (Polars, 5000股×10年 < 2秒)
                     group_backtest (分层回测)
  execution.py    — CostModel (Almgren-Chriss冲击)
                     simulate_execution (组合成交模拟)
  analysis.py     — analyze() TearSheet (20+指标)
                     ic_analysis (因子IC/ICIR/IC衰减)
                     capacity_analysis (策略容量)
  strategies.py   — FactorLongShortStrategy
                     MultiFactorStrategy (多因子等权)
                     BaseStrategy (自定义继承)

Quick start:
  from src.backtest import VectorizedEngine, analyze

  engine = VectorizedEngine(price_df, factor_df)
  result = engine.run(factor="ret_5d", n_long=50, n_short=50)
  tear = analyze(result)

  print(f"Sharpe: {tear.sharpe_ratio}")
  print(f"MaxDD: {tear.max_drawdown}%")
  print(f"ICIR:  {tear.icir}")

与因子库集成:
  from src.factors import compute_factors
  from src.backtest import VectorizedEngine, analyze, ic_analysis

  factors = compute_factors(["ret_5d", "rsi_14", "ma_dev_20d"], ...)
  engine = VectorizedEngine(price_df, factors)
  result = engine.run(factor="ret_5d")
  tear = analyze(result)
"""

from src.backtest.core import VectorizedEngine, BacktestResult, group_backtest
from src.backtest.execution import CostModel, simulate_execution
from src.backtest.analysis import (
    analyze, TearSheet,
    ic_analysis, capacity_analysis,
)
from src.backtest.strategies import (
    BaseStrategy, StrategyConfig,
    FactorLongShortStrategy, MultiFactorStrategy,
)

__all__ = [
    "VectorizedEngine",
    "BacktestResult",
    "group_backtest",
    "CostModel",
    "simulate_execution",
    "analyze",
    "TearSheet",
    "ic_analysis",
    "capacity_analysis",
    "BaseStrategy",
    "StrategyConfig",
    "FactorLongShortStrategy",
    "MultiFactorStrategy",
]
