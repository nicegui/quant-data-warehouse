"""因子库 — 表达式 + 代码双模式因子定义与计算

架构:
  operators.py  — 算子库 (Ref, Mean, Std, RSI, MACD, Rank...)
  engine.py     — 表达式解析器 + 求值引擎
  registry.py   — 因子注册表 (装饰器 API)
  data.py       — Parquet → Polars 数据适配
  compute.py    — 批量计算管道
  evaluate.py   — IC/IR 分析
  definitions/  — 因子定义
    alpha158.py — qlib Alpha158 因子集 (表达式)
    custom.py   — 自定义代码因子
    nlp.py      — NLP/情绪因子 (需先跑 annotator.py)
  annotator.py  — LLM 批量新闻标注管道
  llm/          — LLM 因子挖掘预留接口

Quick start:
  from src.factors import FactorRegistry, register_factor, compute_factors

  # 注册
  @register_factor("momentum", "ret_5d")
  def ret_5d():
      return "Ref($close, -5) / $close - 1"

  # 批量计算 (含NLP因子需先跑标注)
  df = compute_factors(["ret_5d", "rsi_14", "news_sentiment"], start_date="20250101")

  # LLM 发现
  registry = FactorRegistry.to_registry()
"""

from src.factors.operators import OPERATOR_MAP
from src.factors.engine import parse, compute_expression
from src.factors.registry import FactorRegistry, register_factor, Factor
from src.factors.data import load_daily, to_factor_df
from src.factors.compute import compute_factors, export_factors
from src.factors.annotator import NewsAnnotator, AnnotationResult

# 加载因子定义
import src.factors.definitions.alpha158  # noqa: F401
import src.factors.definitions.custom     # noqa: F401
import src.factors.definitions.nlp        # noqa: F401

__all__ = [
    "OPERATOR_MAP",
    "parse",
    "compute_expression",
    "FactorRegistry",
    "register_factor",
    "Factor",
    "load_daily",
    "to_factor_df",
    "compute_factors",
    "export_factors",
]
