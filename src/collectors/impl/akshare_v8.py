"""同行比较 — AkshareV8Collector."""

from __future__ import annotations
import json
import time
from typing import Any
from src.models.akshare_v8 import RawPeerComparison
from src.collectors.base import BaseAKShareCollector

DIMENSIONS = {
    "valuation":   ("估值比较",   "stock_zh_valuation_comparison_em"),
    "growth":      ("成长性比较", "stock_zh_growth_comparison_em"),
    "dupont":      ("杜邦分析",   "stock_zh_dupont_comparison_em"),
    "scale":       ("公司规模",   "stock_zh_scale_comparison_em"),
}


class AkshareV8Collector(BaseAKShareCollector):
    """Batch 8: 同行比较 (估值/成长/杜邦/规模)."""

    def __init__(self):
        super().__init__("akshare_v8")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        symbol = kwargs["symbol"]        # e.g. "SH600519"
        dim_key = kwargs["dimension"]     # e.g. "valuation"
        api_name = DIMENSIONS[dim_key][1]
        api_func = getattr(self.ak, api_name)
        # 同花顺格式: SH600519 / SZ000895
        return self._ak_fetch(api_func, symbol=self._ths_fmt(symbol))

    @staticmethod
    def _ths_fmt(raw: str) -> str:
        """Convert '600519' → 'SH600519', '000895' → 'SZ000895'."""
        raw = raw.strip()
        if raw.startswith(("SH", "SZ")):
            return raw
        if raw.startswith(("6", "9")):
            return f"SH{raw}"
        return f"SZ{raw}"

    def validate(self, raw: list[dict], target_symbol: str = "", dim_key: str = "") -> list[dict]:
        validated = []
        for row in raw:
            code = str(row.get("代码", row.get("股票代码", "")))
            if not code or code in ("行业平均", "行业中值"):
                continue
            rec = {
                "target_symbol": target_symbol,
                "code": code,
                "name": str(row.get("简称", row.get("股票简称", ""))) if row.get("简称") or row.get("股票简称") else None,
                "dimension": dim_key,
                "rank_info": str(row.get("排名", "")) if row.get("排名") else None,
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
            if rec["code"]:
                validated.append(rec)
        return validated

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawPeerComparison, records, ["target_symbol", "dimension", "code"])

    def fetch_symbol(self, symbol: str, delay: float = 0.3) -> int:
        """Fetch all 4 dimensions for one symbol."""
        target_sym = symbol.strip()
        total = 0
        for dim_key, (dim_label, _api_name) in DIMENSIONS.items():
            try:
                raw = self.fetch(symbol=target_sym, dimension=dim_key)
                validated = self.validate(raw, target_symbol=target_sym, dim_key=dim_key)
                n = self.store_raw(validated)
                print(f"  {dim_label}: {n} rows")
                total += n
                time.sleep(delay)
            except Exception as e:
                print(f"  {dim_label}: SKIP ({e})")
        return total

    def run(self, symbols: list[str] | None = None, **kwargs) -> int:
        """Batch run over symbol list."""
        if symbols is None:
            symbols = self._get_active_symbols(limit=200)
        total = 0
        for i, sym in enumerate(symbols):
            print(f"[{i+1}/{len(symbols)}] {sym}")
            total += self.fetch_symbol(sym)
        return total

    def _get_active_symbols(self, limit: int = 200) -> list[str]:
        """Get active A-share symbols from ref_stock_basic."""
        from src.db.engine import get_session
        from src.models.reference import RefStockBasic
        s = get_session()
        try:
            rows = s.query(RefStockBasic.symbol).filter(
                RefStockBasic.list_status == "L"
            ).order_by(RefStockBasic.symbol).limit(limit).all()
            return [r[0] for r in rows]
        finally:
            s.close()
