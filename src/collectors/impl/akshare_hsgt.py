"""沪深港通资金流向 — AkshareHsgtCollector

Non-Tushare collector using akshare.stock_hsgt_hist_em().
"""
from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.akshare_macro import RawAkshareHsgtHist
from src.collectors.base import BaseCollector


class AkshareHsgtCollector(BaseCollector):
    """沪深港通历史资金流向 collector via akshare (non-Tushare)."""

    def __init__(self):
        super().__init__("akshare_hsgt")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch 沪深港通 historical fund flow from akshare."""
        import akshare as ak

        df = ak.stock_hsgt_hist_em()
        if df is None or (hasattr(df, "empty") and df.empty):
            return []
        return df.to_dict(orient="records")

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Chinese field names to English."""
        validated: list[dict[str, Any]] = []
        for row in raw:
            validated.append({
                "date_str": str(row.get("日期", "")),
                "net_buy": self._safe_float(row.get("当日成交净买额")),
                "buy_amount": self._safe_float(row.get("买入成交额")),
                "sell_amount": self._safe_float(row.get("卖出成交额")),
                "cum_net_buy": self._safe_float(row.get("历史累计净买额")),
                "net_flow": self._safe_float(row.get("当日资金流入")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def _safe_float(self, val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Store validated records, deduplicating by date_str."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawAkshareHsgtHist).filter_by(
                    date_str=rec["date_str"]
                ).first()
                if existing:
                    continue
                session.add(RawAkshareHsgtHist(**rec))
                written += 1
        return written
