"""分析师排名 + 跟踪明细 — AnalystCollector

AKShare collectors:
  1. stock_analyst_rank_em(year=...) → raw_analyst_rank
  2. stock_analyst_detail_em(analyst_id=...) → raw_analyst_detail

Usage:
  c = AnalystCollector()
  c.run_rank()      # pull & store annual rankings
  c.run_details()   # pull & store individual coverage (per analyst)
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any

from src.collectors.base import BaseAKShareCollector
from src.models.analyst import RawAnalystRank, RawAnalystDetail


class AnalystCollector(BaseAKShareCollector):
    """Analyst ranking + stock coverage detail collector."""

    def __init__(self):
        super().__init__("analyst_rank")

    # ============================================================
    # RANK: stock_analyst_rank_em
    # ============================================================

    def fetch(self, year: str | None = None, **kwargs) -> list[dict[str, Any]]:
        """Fetch analyst rank for a given year."""
        if year is None:
            year = str(datetime.now().year)
        return self._ak_fetch(self.ak.stock_analyst_rank_em, year=year)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese columns to RawAnalystRank fields."""
        if not raw:
            return []

        ret_annual_key = next(
            (k for k in raw[0].keys() if k.endswith("年收益率") and "最新" not in k), None
        )

        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = {
                "rank": self._safe_int(row.get("序号")),
                "name": self._safe_str(row.get("分析师名称")),
                "org": self._safe_str(row.get("分析师单位")),
                "analyst_id": self._safe_str(row.get("分析师ID")),
                "year_index": self._safe_float(row.get("年度指数")),
                "ret_annual": self._safe_float(row.get(ret_annual_key)) if ret_annual_key else None,
                "ret_3m": self._safe_float(row.get("3个月收益率")),
                "ret_6m": self._safe_float(row.get("6个月收益率")),
                "ret_12m": self._safe_float(row.get("12个月收益率")),
                "stock_count": self._safe_int(row.get("成分股个数")),
                "industry": self._safe_str(row.get("行业")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Dedup by (name, year_index)."""
        if not records:
            return 0
        return self._store_dedup(RawAnalystRank, records, ["name", "year_index"])

    # ============================================================
    # DETAIL: stock_analyst_detail_em
    # ============================================================

    def fetch_detail(self, analyst_id: str) -> list[dict[str, Any]]:
        """Fetch stock coverage detail for one analyst."""
        try:
            df = self.ak.stock_analyst_detail_em(
                analyst_id=analyst_id, indicator="最新跟踪成分股"
            )
            if df is None or df.empty:
                return []
            return df.to_dict(orient="records")
        except Exception:
            return []

    def validate_detail(
        self, raw: list[dict[str, Any]], analyst_id: str
    ) -> list[dict[str, Any]]:
        """Normalize Chinese columns to RawAnalystDetail fields."""
        if not raw:
            return []

        validated: list[dict[str, Any]] = []
        for row in raw:
            rec = {
                "analyst_id": analyst_id,
                "stock_code": self._safe_str(row.get("股票代码")),
                "stock_name": self._safe_str(row.get("股票名称")),
                "entry_date": self._safe_str(row.get("调入日期")),
                "rating_date": self._safe_str(row.get("最新评级日期")),
                "rating": self._safe_str(row.get("当前评级名称")),
                "entry_price": self._safe_float(row.get("成交价格(前复权)")),
                "latest_price": self._safe_float(row.get("最新价格")),
                "pct_chg": self._safe_float(row.get("阶段涨跌幅")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            validated.append(rec)
        return validated

    def store_detail(self, records: list[dict[str, Any]]) -> int:
        """Dedup by (analyst_id, stock_code, entry_date)."""
        if not records:
            return 0
        return self._store_dedup(
            RawAnalystDetail, records, ["analyst_id", "stock_code", "entry_date"]
        )

    def run_rank(self, year: str | None = None) -> int:
        """Full pipeline: fetch → validate → store for rankings."""
        raw = self.fetch(year=year)
        print(f"[analyst_rank] Fetched {len(raw)} analysts")
        validated = self.validate(raw)
        written = self.store_raw(validated)
        print(f"[analyst_rank] Stored {written} (total {len(validated)})")
        return written

    def run_details(self, top_n: int = 50) -> int:
        """Fetch + store stock coverage details for top N ranked analysts.

        Collects from historical rank data already stored in raw_analyst_rank.
        Uses analyst_id from the ranking to query each analyst's coverage.
        """
        from src.db.session import db_session
        ids: list[str] = []
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query(
                f"SELECT analyst_id FROM raw_analyst_rank "
                f"WHERE analyst_id IS NOT NULL AND analyst_id != '' "
                f"GROUP BY analyst_id ORDER BY MIN(rank) LIMIT {top_n}"
            )
            ids = [r["analyst_id"] for r in result if r.get("analyst_id")]
        except Exception:
            try:
                from sqlalchemy import text
                with db_session() as s:
                    r = s.execute(
                        text(
                            "SELECT analyst_id FROM raw_analyst_rank "
                            "WHERE analyst_id IS NOT NULL AND analyst_id != '' "
                            "GROUP BY analyst_id ORDER BY MIN(rank) LIMIT :n"
                        ),
                        {"n": top_n},
                    )
                    ids = [row[0] for row in r]
            except Exception:
                pass

        if not ids:
            print("[analyst_detail] No analyst_ids found in rank data. Run run_rank() first.")
            return 0

        all_written = 0
        for i, aid in enumerate(ids):
            raw = self.fetch_detail(aid)
            if not raw:
                continue
            validated = self.validate_detail(raw, aid)
            written = self.store_detail(validated)
            all_written += written
            if (i + 1) % 10 == 0:
                print(f"[analyst_detail] {i+1}/{len(ids)} analysts, {all_written} stocks stored")
            time.sleep(0.3)  # rate limit

        print(f"[analyst_detail] Done: {len(ids)} analysts, {all_written} stocks total")
        return all_written

    # ── Helpers ──

    @staticmethod
    def _safe_int(val: Any) -> int | None:
        if val is None:
            return None
        try:
            return int(float(str(val)))
        except (ValueError, TypeError):
            return None
