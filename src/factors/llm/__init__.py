"""LLM 因子挖掘预留模块

架构设计:
  1. LLM 生成因子表达式字符串 → 直接注册 → 批量回测
  2. LLM 阅读论文 → 提取公式 → 翻译为表达式或代码
  3. LLM 组合现有因子 → 高阶交互因子

当前状态: 接口预留，具体 LLM 调用在外部 agent 层实现。

使用流程:
  from src.factors.llm import discover, paper_to_factor

  # 1. LLM 挖掘: 给出候选表达式
  candidates = await discover("挖掘动量反转因子", existing_factors=...)

  # 2. 论文复现: 给定论文摘要生成因子
  factor = await paper_to_factor(paper_abstract="...")

  # 3. 候选因子可以通过 backtest 验证
  from src.factors.evaluate import ic_analysis
  ic_analysis(candidate_df, forward_returns)
"""

from __future__ import annotations

from src.factors.registry import FactorRegistry


def get_registry_for_llm() -> dict:
    """导出因子注册表供 LLM 消费。

    返回格式:
    {
      "ret_5d": {"category": "momentum", "expression": "Ref($close, -5) / $close - 1", ...},
      ...
    }
    """
    return FactorRegistry.to_registry()


def get_available_operators() -> dict:
    """导出可用算子供 LLM 了解系统能力。

    返回格式:
    {
      "Ref": "(series, n) -> series shifted by n",
      "Mean": "(series, window) -> rolling mean",
      ...
    }
    """
    from src.factors.operators import OPERATOR_MAP

    return {
        name: fn.__doc__ or f"Operator: {name}"
        for name, (fn, _) in OPERATOR_MAP.items()
    }


def get_available_columns() -> list[str]:
    """导出可用数据列供 LLM 了解特征空间。"""
    return [
        "open", "high", "low", "close", "volume", "amount",
        "vwap", "turnover_rate", "pre_close", "pct_chg",
        "adj_factor", "total_mv", "circ_mv", "pe", "pb", "ps",
    ]


# ── 预留接口 ──

async def discover(
    prompt: str,
    existing_factors: list[str] | None = None,
    max_candidates: int = 20,
) -> list[dict]:
    """LLM 因子挖掘。

    Args:
        prompt: 挖掘方向描述
        existing_factors: 已有因子列表 (避免重复)
        max_candidates: 最大候选数

    Returns:
        [{name, expression, category, rationale}, ...]

    实现思路:
      1. 构建 prompt: system="你是量化因子挖掘专家...", operators=..., columns=...
      2. LLM 生成候选表达式
      3. 解析验证每个表达式
      4. 返回有效候选
    """
    raise NotImplementedError(
        "LLM factor discovery requires external agent integration.\n"
        "Use the factor registry + operators info to build your discovery prompt."
    )


async def paper_to_factor(
    paper_text: str,
    verify: bool = True,
) -> dict:
    """论文 → 因子。

    Args:
        paper_text: 论文摘要或方法部分
        verify: 是否验证表达式可解析

    Returns:
        {name, expression, category, paper_ref, verified}

    实现思路:
      1. LLM 提取论文中的公式
      2. 翻译为因子表达式
      3. parse 验证
      4. 如有复杂逻辑，生成 impl="code" 的 Python 代码
    """
    raise NotImplementedError(
        "Paper-to-factor requires external agent integration."
    )
