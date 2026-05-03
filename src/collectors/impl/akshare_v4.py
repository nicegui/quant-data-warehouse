"""全球宏观+LPR+可转债+期权+ETF+失业率 — AkshareV4Collector."""

from __future__ import annotations
import json
from typing import Any
from src.models.akshare_v4 import (
    RawGlobalMacro, RawLprRate, RawCbIndex,
    RawHs300Option, RawEtfScale, RawUnemployment,
)
from src.collectors.base import BaseAKShareCollector


class AkshareV4Collector(BaseAKShareCollector):
    """Batch 4: 全球宏观+利率+转债+期权+ETF."""

    def __init__(self):
        super().__init__("akshare_v4")

    def fetch(self, sub_api: str = "usa_cpi", **kwargs) -> list[dict[str, Any]]:
        # USA macro (cal format)
        if sub_api == "usa_cpi":
            return self._mk("usa_cpi", self.ak.macro_usa_cpi_monthly)
        if sub_api == "usa_nfp":
            return self._mk("usa_nfp", self.ak.macro_usa_non_farm)
        if sub_api == "usa_unemp":
            return self._mk("usa_unemp", self.ak.macro_usa_unemployment_rate)
        if sub_api == "usa_conf":
            return self._mk("usa_conf", self.ak.macro_usa_cb_consumer_confidence)
        if sub_api == "usa_gdp":
            return self._mk("usa_gdp", self.ak.macro_usa_gdp_monthly)
        if sub_api == "usa_retail":
            return self._mk("usa_retail", self.ak.macro_usa_retail_sales)
        if sub_api == "usa_trade":
            return self._mk("usa_trade", self.ak.macro_usa_trade_balance)
        # Europe
        if sub_api == "euro_cpi":
            return self._mk("euro_cpi", self.ak.macro_euro_cpi_yoy)
        if sub_api == "euro_gdp":
            return self._mk("euro_gdp", self.ak.macro_euro_gdp_yoy)
        # Japan
        if sub_api == "japan_rate":
            return self._jp("japan_rate", self.ak.macro_japan_bank_rate)
        if sub_api == "japan_cpi":
            return self._jp("japan_cpi", self.ak.macro_japan_cpi_yearly)
        # Others
        if sub_api == "lpr":
            return self._ak_fetch(self.ak.macro_china_lpr)
        if sub_api == "cb_index":
            return self._ak_fetch(self.ak.bond_cb_index_jsl)
        if sub_api == "hs300_option":
            r = self._ak_fetch(self.ak.option_cffex_hs300_spot_sina)
            today = kwargs.get("date", "")
            for row in r:
                row["_date"] = today
            return r
        if sub_api == "etf_scale":
            return self._ak_fetch(self.ak.fund_etf_scale_sse)
        if sub_api == "unemployment":
            return self._ak_fetch(self.ak.macro_china_urban_unemployment)
        raise ValueError(f"Unknown sub_api: {sub_api}")

    def _mk(self, src: str, fn) -> list[dict]:
        rows = self._ak_fetch(fn)
        for r in rows:
            r["_source"] = src
        return rows

    def _jp(self, src: str, fn) -> list[dict]:
        """Japan format: 时间/前值/现值/发布日期 → cal format."""
        rows = self._ak_fetch(fn)
        result = []
        for r in rows:
            result.append({
                "_source": src,
                "item": str(r.get("时间", "")),
                "date_str": str(r.get("发布日期", "")),
                "value": self._sf(r.get("现值")),
                "forecast": None,
                "previous": self._sf(r.get("前值")),
            })
        return result

    # ── Validate ──

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            rec = self._norm(row)
            if rec:
                validated.append(rec)
        return validated

    def _norm(self, row: dict) -> dict | None:
        # Global macro calendar
        if "_source" in row:
            return {
                "source": str(row["_source"]),
                "item": str(row.get("商品", row.get("item", ""))),
                "date_str": str(row.get("日期", row.get("date_str", ""))),
                "value": self._sf(row.get("今值", row.get("value"))),
                "forecast": self._sf(row.get("预测值", row.get("forecast"))),
                "previous": self._sf(row.get("前值", row.get("previous"))),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        # LPR
        if "LPR1Y" in row:
            return {
                "trade_date": str(row.get("TRADE_DATE", "")),
                "lpr_1y": self._sf(row.get("LPR1Y")),
                "lpr_5y": self._sf(row.get("LPR5Y")),
                "rate_1": self._sf(row.get("RATE_1")),
                "rate_2": self._sf(row.get("RATE_2")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        # CB index
        if "increase_rt" in row:
            return {
                "price_date": str(row.get("price_dt", "")),
                "price": self._sf(row.get("price")),
                "amount": self._sf(row.get("amount")),
                "volume": self._sf(row.get("volume")),
                "count": int(row["count"]) if row.get("count") else None,
                "increase_val": self._sf(row.get("increase_val")),
                "increase_rt": self._sf(row.get("increase_rt")),
                "avg_price": self._sf(row.get("avg_price")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        # HS300 option
        if "看涨合约-买量" in row:
            calls = self._opt(row, "CALL", "看涨合约")
            puts = self._opt(row, "PUT", "看跌合约")
            return [calls, puts] if calls and puts else calls or puts
        # ETF scale
        if "ETF类型" in row:
            return {
                "fund_code": str(row.get("基金代码", "")),
                "fund_name": str(row.get("基金简称", "")) if row.get("基金简称") else None,
                "etf_type": str(row.get("ETF类型", "")) if row.get("ETF类型") else None,
                "stat_date": str(row.get("统计日期", "")),
                "shares": self._sf(row.get("基金份额")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        # Unemployment
        if "date" in row and "item" in row and "value" in row:
            return {
                "date_str": str(row["date"]),
                "item": str(row["item"]),
                "value": self._sf(row.get("value")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            }
        return {"raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _opt(self, row: dict, otype: str, prefix: str) -> dict | None:
        strike = row.get("行权价")
        if strike is None:
            return None
        return {
            "trade_date": str(row.get("_date", "")),
            "opt_type": otype,
            "strike": float(strike),
            "buy_vol": self._sf(row.get(f"{prefix}-买量")),
            "bid": self._sf(row.get(f"{prefix}-买价")),
            "last": self._sf(row.get(f"{prefix}-最新价")),
            "ask": self._sf(row.get(f"{prefix}-卖价")),
            "sell_vol": self._sf(row.get(f"{prefix}-卖量")),
            "position": self._sf(row.get(f"{prefix}-持仓量")),
            "change": self._sf(row.get(f"{prefix}-涨跌")),
            "raw_json": json.dumps(row, ensure_ascii=False, default=str),
        }

    @staticmethod
    def _sf(val):
        try:
            return float(val) if val not in (None, "") else None
        except:
            return None

    # ── Store ──

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        # Flatten option records (CALL+PUT returned as list)
        flat = []
        for r in records:
            if isinstance(r, list):
                flat.extend(r)
            else:
                flat.append(r)
        if not flat:
            return 0

        f = flat[0]
        if "source" in f:
            return self._store_dedup(RawGlobalMacro, flat, ["source", "item", "date_str"])
        if "lpr_1y" in f:
            return self._store_dedup(RawLprRate, flat, ["trade_date"])
        if "increase_rt" in f:
            return self._store_dedup(RawCbIndex, flat, ["price_date"])
        if "strike" in f:
            return self._store_dedup(RawHs300Option, flat, ["trade_date", "strike", "opt_type"])
        if "etf_type" in f:
            return self._store_dedup(RawEtfScale, flat, ["fund_code", "stat_date"])
        if "item" in f and "date_str" in f and "value" in f:
            return self._store_dedup(RawUnemployment, flat, ["date_str", "item"])
        return 0
