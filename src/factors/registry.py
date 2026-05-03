"""因子注册表 — 支持表达式因子和代码因子

两种注册方式：

1. 表达式因子 (推荐，可被 LLM 自动挖掘):
    @register_factor("momentum", "ret_5d", impl="expr")
    def ret_5d():
        return "Ref($close, -5) / $close - 1"

2. 代码因子 (复杂逻辑，需要 Python 实现):
    @register_factor("custom", "overnight_gap", impl="code")
    class OvernightGap:
        def compute(self, df: pl.DataFrame) -> pl.Series:
            return df["open"] / df["close"].shift(1) - 1

注册表用途：
  - 列出所有可用因子
  - 按类别分组
  - LLM 挖掘时发现已有因子避免重复
  - 论文复现标注来源
"""

from __future__ import annotations

import polars as pl
from dataclasses import dataclass, field
from typing import Callable, ClassVar, Optional

from src.factors.engine import compute_expression


# ═══════════════════════════════════════════
# 因子定义数据类
# ═══════════════════════════════════════════

@dataclass
class Factor:
    """因子元数据。"""

    name: str                        # e.g. "ret_5d"
    category: str                    # momentum / volatility / volume / valuation / ...
    impl: str = "expr"               # "expr" or "code"
    expression: str | None = None    # 表达式字符串 (impl="expr")
    code_compute: Callable | None = None  # 代码因子 compute 函数 (impl="code")
    paper_ref: str | None = None     # 论文出处
    description: str = ""            # 因子说明

    def compute(self, df: pl.DataFrame) -> pl.Series:
        """在 DataFrame 上计算该因子。"""
        if self.impl == "expr" and self.expression:
            return compute_expression(self.expression, df)
        if self.impl == "code" and self.code_compute:
            return self.code_compute(df)
        raise ValueError(f"Factor {self.name}: no implementation")


# ═══════════════════════════════════════════
# 注册表
# ═══════════════════════════════════════════

class FactorRegistry:
    """因子注册中心。"""

    _factors: ClassVar[dict[str, Factor]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        category: str,
        *,
        impl: str = "expr",
        expression: str | None = None,
        code_fn: Callable | None = None,
        paper_ref: str | None = None,
        description: str = "",
    ) -> "Factor":
        """注册一个因子 (显式 API)。"""
        if name in cls._factors:
            raise ValueError(f"Factor '{name}' already registered")

        factor = Factor(
            name=name,
            category=category,
            impl=impl,
            expression=expression,
            code_compute=code_fn,
            paper_ref=paper_ref,
            description=description,
        )
        cls._factors[name] = factor
        return factor

    @classmethod
    def get(cls, name: str) -> Factor | None:
        return cls._factors.get(name)

    @classmethod
    def list(cls, category: str | None = None) -> list[Factor]:
        """列出所有因子，可按类别过滤。"""
        factors = list(cls._factors.values())
        if category:
            factors = [f for f in factors if f.category == category]
        return factors

    @classmethod
    def categories(cls) -> list[str]:
        return sorted({f.category for f in cls._factors.values()})

    @classmethod
    def to_registry(cls) -> dict:
        """导出注册表为 dict (供 LLM 消费)。"""
        return {
            name: {
                "name": f.name,
                "category": f.category,
                "impl": f.impl,
                "expression": f.expression,
                "paper_ref": f.paper_ref,
                "description": f.description,
            }
            for name, f in cls._factors.items()
        }


# ═══════════════════════════════════════════
# 装饰器 API
# ═══════════════════════════════════════════

def register_factor(
    category: str = "custom",
    name: str | None = None,
    *,
    impl: str = "expr",
    paper_ref: str | None = None,
    description: str = "",
):
    """装饰器: 注册表达式因子或代码因子。

    用法:
        # 表达式因子
        @register_factor("momentum", "ret_5d")
        def ret_5d():
            return "Ref($close, -5) / $close - 1"

        # 代码因子
        @register_factor("custom", "overnight_gap", impl="code")
        def overnight_gap(df: pl.DataFrame) -> pl.Series:
            return df["open"] / df["close"].shift(1) - 1
    """

    def decorator(fn_or_cls):
        factor_name = name or fn_or_cls.__name__

        if impl == "expr":
            # 表达式因子: 调用 fn -> 返回表达式字符串
            expr_str = fn_or_cls()
            FactorRegistry.register(
                name=factor_name,
                category=category,
                impl="expr",
                expression=expr_str,
                paper_ref=paper_ref,
                description=description or fn_or_cls.__doc__ or "",
            )
        else:
            # 代码因子: fn 就是 compute 函数
            FactorRegistry.register(
                name=factor_name,
                category=category,
                impl="code",
                code_fn=fn_or_cls,
                paper_ref=paper_ref,
                description=description or (fn_or_cls.__doc__ or ""),
            )
        return fn_or_cls

    return decorator
