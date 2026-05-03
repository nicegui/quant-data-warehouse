"""回测策略 — 因子策略 + 自定义策略基类

内置:
  - FactorLongShortStrategy: 因子排序，long top-N, short bottom-N
  - FactorQuantileStrategy: 分层回测
  - CustomStrategy: 继承实现自己逻辑
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import polars as pl

from src.backtest.core import VectorizedEngine, BacktestResult


# ═══════════════════════════════════════════
# 策略基类
# ═══════════════════════════════════════════

@dataclass
class StrategyConfig:
    """策略配置。"""
    n_long: int = 50
    n_short: int = 50
    rebalance_freq: int = 20           # 调仓频率 (天)
    commission: float = 0.0003
    slippage: float = 0.001
    max_weight: float = 0.1            # 单股权重上限
    start_date: str | None = None
    end_date: str | None = None


class BaseStrategy(ABC):
    """回测策略基类。

    继承并实现 generate_signals() 返回每期目标权重。
    """

    def __init__(self, config: StrategyConfig | None = None):
        self.config = config or StrategyConfig()

    @abstractmethod
    def generate_signals(
        self,
        factor_df: pl.DataFrame,
        price_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """生成交易信号。

        Returns:
            DataFrame: trade_date, ts_code, weight (正=多, 负=空, 0=平)
        """
        ...

    def run(
        self,
        factor_df: pl.DataFrame,
        price_df: pl.DataFrame,
    ) -> BacktestResult:
        """运行策略回测。"""
        engine = VectorizedEngine(price_df, factor_df)
        signals = self.generate_signals(factor_df, price_df)

        # If strategy generates weights directly, convert to long/short
        return engine.run(
            factor=signals["weight"],
            n_long=self.config.n_long,
            n_short=self.config.n_short,
            rebalance_freq=self.config.rebalance_freq,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            commission=self.config.commission,
            slippage=self.config.slippage,
            max_weight=self.config.max_weight,
            factor_df=signals.rename({"weight": "_factor"}),
        )


# ═══════════════════════════════════════════
# 因子多空策略
# ═══════════════════════════════════════════

class FactorLongShortStrategy(BaseStrategy):
    """因子多空策略 — 按因子值排序，long top-N, short bottom-N。

    与直接用 engine.run(factor=...) 等价，只是封装成策略类。
    """

    def __init__(
        self,
        factor: str,
        config: StrategyConfig | None = None,
    ):
        super().__init__(config)
        self.factor = factor

    def generate_signals(
        self,
        factor_df: pl.DataFrame,
        price_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """因子值直接作为信号（越大越做多）。"""
        return factor_df.select(["ts_code", "trade_date"]).with_columns(
            factor_df[self.factor].alias("weight")
        )

    def run(
        self,
        factor_df: pl.DataFrame,
        price_df: pl.DataFrame,
    ) -> BacktestResult:
        engine = VectorizedEngine(price_df, factor_df)
        return engine.run(
            factor=self.factor,
            n_long=self.config.n_long,
            n_short=self.config.n_short,
            rebalance_freq=self.config.rebalance_freq,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            commission=self.config.commission,
            slippage=self.config.slippage,
            max_weight=self.config.max_weight,
        )


# ═══════════════════════════════════════════
# 多因子合成策略
# ═══════════════════════════════════════════

class MultiFactorStrategy(BaseStrategy):
    """多因子等权合成策略。

    多个因子 z-score 标准化后等权加总。
    """

    def __init__(
        self,
        factors: list[str],
        config: StrategyConfig | None = None,
    ):
        super().__init__(config)
        self.factors = factors

    def generate_signals(
        self,
        factor_df: pl.DataFrame,
        price_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """多因子 z-score → 等权加总。"""
        # Z-score per date
        combined = factor_df.select(["ts_code", "trade_date"])
        composite = pl.Series("composite", [0.0] * factor_df.height)

        for f in self.factors:
            if f not in factor_df.columns:
                continue
            # Cross-sectional z-score
            z = (
                factor_df.select(["ts_code", "trade_date", f])
                .with_columns([
                    ((pl.col(f) - pl.col(f).mean().over("trade_date"))
                     / pl.col(f).std().over("trade_date")).alias(f"{f}_z")
                ])
                .get_column(f"{f}_z")
            )
            composite = composite + z.fill_null(0)

        return combined.with_columns(composite.alias("weight"))
