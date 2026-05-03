"""宏观高频指标 — AkshareV10Collector.

23个API: 房价/景气/税收/保险/手机/菜篮子/农产品/农副/能源/费城半导体/
义乌电子/建材/建材价格/物流景气/BDTI/BSI/BCI/BDI/BPI/BCTI/新增信贷/大宗商品
"""

from __future__ import annotations
import json
from typing import Any
import pandas as pd
from src.models.akshare_v10 import RawMacroIndicator
from src.collectors.base import BaseAKShareCollector


# Standard 8-col APIs: (日期, 最新值, 涨跌幅, 近3月, 近6月, 近1年, 近2年, 近3年)
STD_8COL = {
    "insurance":      ("保险收入",     "macro_china_insurance_income"),
    "mobile":         ("手机出货量",   "macro_china_mobile_number"),
    "vegetable":      ("菜篮子",       "macro_china_vegetable_basket"),
    "agri_product":   ("农产品批发",   "macro_china_agricultural_product"),
    "agri_index":     ("农副指数",     "macro_china_agricultural_index"),
    "energy_index":   ("能源指数",     "macro_china_energy_index"),
    "sox":            ("费城半导体",   "macro_global_sox_index"),
    "yw_electronic":  ("义乌电子",     "macro_china_yw_electronic_index"),
    "construction":   ("建材指数",     "macro_china_construction_index"),
    "construct_price":("建材价格",     "macro_china_construction_price_index"),
    "lpi":            ("物流景气",     "macro_china_lpi_index"),
    "bdti":           ("原油运输BDTI", "macro_china_bdti_index"),
    "bsi":            ("超灵便BSI",    "macro_china_bsi_index"),
    "bci":            ("海岬型BCI",    "macro_shipping_bci"),
    "bdi":            ("干散货BDI",    "macro_shipping_bdi"),
    "bpi":            ("巴拿马BPI",    "macro_shipping_bpi"),
    "bcti":           ("成品油BCTI",   "macro_shipping_bcti"),
    "commodity":      ("大宗商品",     "macro_china_commodity_price_index"),
}

# APIs with special formats
SPECIAL = [
    # (key, label, api_name, date_col, value_col, change_col, sub_key_func)
    ("house_price", "房价", "macro_china_new_house_price", "日期", "新建商品住宅价格指数-同比", None, lambda r: r.get("城市", "")),
    ("enterprise_boom", "企业景气", "macro_china_enterprise_boom_index", "季度", "企业景气指数-指数", "企业景气指数-同比", lambda r: ""),
    ("tax", "税收收入", "macro_china_national_tax_receipts", "季度", "税收收入合计", "较上年同期", lambda r: ""),
    ("credit", "新增信贷", "macro_china_new_financial_credit", "月份", "当月", "当月-同比增长", lambda r: ""),
]


class AkshareV10Collector(BaseAKShareCollector):
    """Batch 10: 宏观高频指标."""

    def __init__(self):
        super().__init__("akshare_v10")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    def _fetch_8col(self, api_name: str, source: str) -> list[dict]:
        """Parse standard 8-column format."""
        fn = getattr(self.ak, api_name)
        df = fn()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": source,
                "date": str(row["日期"])[:16],
                "sub_key": "",
                "value": float(row["最新值"]) if not pd.isna(row["最新值"]) else None,
                "change_pct": float(row["涨跌幅"]) if not pd.isna(row.get("涨跌幅")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    def _fetch_special(self, api_name: str, source: str, date_col: str,
                        value_col: str, change_col: str | None,
                        sub_key_fn) -> list[dict]:
        """Parse special-format APIs."""
        fn = getattr(self.ak, api_name)
        # Some special APIs take extra params
        try:
            df = fn()
        except TypeError:
            # house_price needs city args
            df = fn(city_first="北京", city_second="上海")

        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            v = row.get(value_col)
            chg = row.get(change_col) if change_col else None
            records.append({
                "source": source,
                "date": str(row[date_col])[:16],
                "sub_key": str(sub_key_fn(row)) if sub_key_fn else "",
                "value": float(v) if v is not None and not pd.isna(v) else None,
                "change_pct": float(chg) if chg is not None and not pd.isna(chg) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawMacroIndicator, records, ["source", "date", "sub_key"])

    def run(self, **kwargs) -> int:
        total = 0

        # Standard 8-col APIs
        for key, (label, api_name) in STD_8COL.items():
            try:
                records = self._fetch_8col(api_name, key)
                n = self.store_raw(records)
                print(f"  {label}: {n} rows")
                total += n
            except Exception as e:
                print(f"  {label}: SKIP ({e})")

        # Special format APIs
        for key, label, api_name, dc, vc, cc, skf in SPECIAL:
            try:
                records = self._fetch_special(api_name, key, dc, vc, cc, skf)
                n = self.store_raw(records)
                print(f"  {label}: {n} rows")
                total += n
            except Exception as e:
                print(f"  {label}: SKIP ({e})")

        print(f"\nTotal: {total} rows")
        return total
