"""LLM 文本标注管道 — 批量新闻 → 情绪/事件标签

跑一次，持久化到 parquet。因子计算时只读标注结果，不调 LLM。

支持:
  - 批量标注 (OpenAI / 本地模型 / Hermes agent)
  - 增量标注 (只处理新文本)
  - 多标签输出 (sentiment / event_type / impact / entities)
"""

from __future__ import annotations

import json
import polars as pl
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class AnnotationResult:
    """单条新闻的 LLM 标注结果。"""
    news_id: str
    ts_code: str           # 关联股票
    pub_date: str          # YYYYMMDD
    sentiment: float       # -1.0 ~ 1.0 (负→正)
    event_type: str        # earnings|policy|merger|lawsuit|product|macro|other
    impact: float          # 0~1 影响力
    summary: str           # 一句话摘要
    keywords: list[str]    # 关键实体/主题
    raw_response: str      # LLM 原始输出 (审计用)


# ═══════════════════════════════════════════
# 标注管道
# ═══════════════════════════════════════════

class NewsAnnotator:
    """批量新闻 LLM 标注器。

    Usage:
        annotator = NewsAnnotator(llm_fn=my_openai_fn)
        annotator.annotate_batch(news_df, output_path="data/annotations/")
    """

    def __init__(
        self,
        llm_fn: Callable[[str], str] | None = None,
        batch_size: int = 10,
    ):
        """
        Args:
            llm_fn: LLM 调用函数，输入 prompt，输出 JSON 字符串。
                   不传则使用内置 Hermes agent 模式（后续实现）。
            batch_size: 每批标注条数
        """
        self.llm = llm_fn
        self.batch_size = batch_size

    def annotate_batch(
        self,
        df: pl.DataFrame,
        output_dir: str | Path,
        *,
        text_col: str = "content",
        id_col: str = "datetime",
        resume: bool = True,
    ) -> pl.DataFrame:
        """批量标注新闻 DataFrame。

        Args:
            df: 新闻 DataFrame，至少含 content 列
            output_dir: 标注结果输出目录
            text_col: 文本列名
            id_col: 唯一标识列名
            resume: 是否跳过已标注

        Returns:
            标注结果 DataFrame
        """
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        cache_path = output / "annotations.parquet"

        # Load existing annotations for resume
        done_ids: set[str] = set()
        if resume and cache_path.exists():
            existing = pl.read_parquet(cache_path)
            done_ids = set(existing[id_col].to_list())

        results: list[dict] = []
        to_process = df.filter(~pl.col(id_col).is_in(list(done_ids))) if done_ids else df

        for start in range(0, len(to_process), self.batch_size):
            batch = to_process[start:start + self.batch_size]
            for row in batch.iter_rows(named=True):
                try:
                    ann = self._annotate_one(row, text_col, id_col)
                    if ann:
                        results.append({
                            id_col: ann.news_id,
                            "ts_code": ann.ts_code,
                            "pub_date": ann.pub_date,
                            "sentiment": ann.sentiment,
                            "event_type": ann.event_type,
                            "impact": ann.impact,
                            "summary": ann.summary,
                            "keywords": json.dumps(ann.keywords, ensure_ascii=False),
                            "raw_response": ann.raw_response,
                        })
                except Exception as e:
                    print(f"[WARN] Annotation failed for {row.get(id_col, '?')}: {e}")

        # Save
        new_df = pl.DataFrame(results) if results else pl.DataFrame()
        if resume and cache_path.exists():
            combined = pl.concat([existing, new_df])
            combined.write_parquet(cache_path)
            return combined
        else:
            new_df.write_parquet(cache_path)
            return new_df

    def _annotate_one(
        self, row: dict, text_col: str, id_col: str
    ) -> AnnotationResult | None:
        """标注单条新闻。"""
        text = row.get(text_col, "")
        if not text or len(str(text)) < 10:
            return None

        prompt = _build_annotation_prompt(str(text))
        response = self.llm(prompt) if self.llm else _mock_llm_response(text)

        return _parse_llm_response(
            response,
            news_id=str(row.get(id_col, "")),
            text=text,
        )


# ═══════════════════════════════════════════
# Prompt 模板
# ═══════════════════════════════════════════

def _build_annotation_prompt(text: str) -> str:
    return f"""分析以下财经新闻，返回 JSON：

{{
  "sentiment": -1.0到1.0之间的数值（负→正），
  "event_type": "earnings|policy|merger|lawsuit|product|macro|other",
  "impact": 0到1之间的影响力数值，
  "summary": "一句话中文摘要",
  "keywords": ["关键实体1", "关键词2"],
  "ts_code": "关联股票代码(如000001.SZ)，无法确定则为空"
}}

新闻：
{text[:2000]}"""


def _parse_llm_response(
    response: str, news_id: str, text: str = ""
) -> AnnotationResult:
    """解析 LLM JSON 响应为 AnnotationResult。"""
    # Extract JSON from response (may have markdown wrapping)
    resp = response.strip()
    if "```json" in resp:
        resp = resp.split("```json")[1].split("```")[0]
    elif "```" in resp:
        resp = resp.split("```")[1].split("```")[0]

    data = json.loads(resp)
    return AnnotationResult(
        news_id=news_id,
        ts_code=data.get("ts_code", ""),
        pub_date="",  # filled by caller
        sentiment=float(data.get("sentiment", 0)),
        event_type=str(data.get("event_type", "other")),
        impact=float(data.get("impact", 0)),
        summary=str(data.get("summary", "")),
        keywords=list(data.get("keywords", [])),
        raw_response=response,
    )


def _mock_llm_response(text: str) -> str:
    """Mock LLM for testing — returns neutral. 生产环境替换为真实 LLM。"""
    return json.dumps({
        "sentiment": 0.0,
        "event_type": "other",
        "impact": 0.1,
        "summary": text[:50],
        "keywords": [],
        "ts_code": "",
    }, ensure_ascii=False)
