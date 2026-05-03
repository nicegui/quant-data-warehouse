"""创新高排名 — AkshareV7Collector."""

from __future__ import annotations
import json
from typing import Any
from src.models.akshare_v7 import RawStockCxg
from src.collectors.base import BaseAKShareCollector

SYMBOLS = ["创月新高", "半年新高", "一年新高", "历史新高"]


class AkshareV7Collector(BaseAKShareCollector):
    """Batch 7: 创新高排名."""

    def __init__(self):
        super().__init__("akshare_v7")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        symbol = kwargs.get("symbol", "创月新高")
        return self._ak_fetch(self.ak.stock_rank_cxg_ths, symbol=symbol)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = {
                "code": str(row.get("股票代码", "")),
                "name": str(row.get("股票简称", "")) if row.get("股票简称") else None,
                "symbol": str(row.get("symbol", "")),
                "change_pct": self._sf(row.get("涨跌幅")),
                "turnover_rate": self._sf(row.get("换手率")),
                "latest_price": self._sf(row.get("最新价")),
                "prev_high": self._sf(row.get("前期高点")),
                "prev_high_date": row.get("前期高点日期"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            if rec["code"]:
                validated.append(rec)
        return validated

    @staticmethod
    def _sf(val):
        try:
            return float(val) if val is not None and val != "" else None
        except (ValueError, TypeError):
            return None

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawStockCxg, records, ["code", "symbol"])

    def run(self, **kwargs) -> int:
        """Fetch all 4 symbol types and store."""
        total = 0
        for sym in SYMBOLS:
            raw = self.fetch(symbol=sym)
            # Inject symbol into records
            for r in raw:
                r["symbol"] = sym
            validated = self.validate(raw)
            n = self.store_raw(validated)
            print(f"  {sym}: {n} rows")
            total += n
        return total
