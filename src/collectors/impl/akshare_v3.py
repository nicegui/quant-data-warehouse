"""BDI航运+商品价格+国债+回购+工业+热搜+汇率+美股S&P500 — AkshareV3Collector."""

from __future__ import annotations

import json
import time
from typing import Any

from src.models.akshare_v3 import (
    RawShippingIndex, RawCommodityPrice, RawYieldCurve,
    RawRepoRate, RawIndustrialProduction, RawBaiduHotSearch,
    RawFxSpot, RawUsStockDaily,
)
from src.collectors.base import BaseAKShareCollector


class AkshareV3Collector(BaseAKShareCollector):
    """Batch 3: 航运+商品+利率+工业+热搜+汇率+美股."""

    checkpoint_key = "akshare_v3_us"

    def __init__(self):
        super().__init__("akshare_v3")

    def fetch(self, sub_api: str = "shipping", **kwargs) -> list[dict[str, Any]]:
        if sub_api == "shipping":
            rows = []
            for name, fn in [("BDI", self.ak.macro_shipping_bdi), ("BCI", self.ak.macro_shipping_bci)]:
                try:
                    data = self._ak_fetch(fn)
                    for r in data:
                        r["_index_type"] = name
                    rows.extend(data)
                except Exception as e:
                    print(f"[v3] {name} failed: {e}")
            return rows

        elif sub_api == "commodity":
            return self._ak_fetch(self.ak.macro_china_commodity_price_index)

        elif sub_api == "yield_curve":
            rows = self._ak_fetch(self.ak.bond_china_close_return_map)
            # Flatten: {"2025-01-01": {"1Y": 1.5, "10Y": 2.8}}
            result = []
            import json as _json
            for item in rows:
                for date_str, curve in item.items():
                    if isinstance(curve, dict):
                        for term, val in curve.items():
                            result.append({
                                "date": date_str,
                                "term": term,
                                "value": val,
                            })
            return result

        elif sub_api == "repo":
            return self._ak_fetch(self.ak.repo_rate_query)

        elif sub_api == "industrial":
            return self._ak_fetch(self.ak.macro_china_industrial_production_yoy)

        elif sub_api == "baidu_hot":
            rows = []
            dates = kwargs.get("dates", ["2024-01-01", "2024-06-01", "2024-12-01", "2025-01-01"])
            for d in dates:
                try:
                    data = self._ak_fetch(self.ak.stock_hot_search_baidu, date=d)
                    for r in data:
                        r["_date"] = d
                    rows.extend(data)
                except Exception as e:
                    print(f"[v3] baidu {d} failed: {e}")
                time.sleep(0.3)
            return rows

        elif sub_api == "fx_spot":
            return self._ak_fetch(self.ak.fx_spot_quote)

        elif sub_api == "us_stocks":
            return self._fetch_sp500(**kwargs)

        else:
            raise ValueError(f"Unknown sub_api: {sub_api}")

    def _fetch_sp500(self, **kwargs) -> list[dict[str, Any]]:
        """Pull S&P 500 components' daily history."""
        # Get S&P 500 ticker list
        import akshare as ak
        start = kwargs.get("start_date", "20240101")
        end = kwargs.get("end_date", "20241231")

        # Try to get SP500 components
        try:
            df_sp = ak.index_us_stock_sina(symbol=".INX")
            # This returns the index OHLCV, not components. Try another source.
            df_sp = ak.stock_us_spot_em()
            tickers = list(df_sp["代码"])
            print(f"[v3] SP500: {len(tickers)} tickers from spot list")
        except Exception:
            # Fallback: major SP500 tickers
            tickers = ["105.AAPL", "105.MSFT", "105.GOOGL", "105.AMZN", "105.NVDA",
                       "105.META", "105.TSLA", "105.BRK.B", "105.JPM", "105.V"]
            print(f"[v3] SP500: fallback list of {len(tickers)} tickers")

        all_rows = []
        total = len(tickers)
        for i, sym in enumerate(tickers):
            try:
                df = ak.stock_us_hist(symbol=sym, period="daily", start_date=start, end_date=end)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        all_rows.append({"_symbol": sym, **row.to_dict()})
            except Exception as e:
                if i < 5:
                    print(f"[v3] us {sym}: {e}")
            if (i + 1) % 50 == 0:
                print(f"[v3] us progress: {i+1}/{total}, rows={len(all_rows)}")
            time.sleep(0.05)

        print(f"[v3] us Done: {total}, {len(all_rows)} rows")
        return all_rows

    # ── Validate ──

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            rec = self._normalize(row)
            if rec:
                validated.append(rec)
        return validated

    def _normalize(self, row: dict) -> dict | None:
        if "_index_type" in row:
            return self._norm_shipping(row)
        if "近3月涨跌幅" in row and "_index_type" not in row:
            return self._norm_price(row)
        if "_symbol" in row:
            return self._norm_us(row)
        if "date" in row and "term" in row:
            return self._norm_yield(row)
        if "FR001" in row:
            return self._norm_repo(row)
        if "预测值" in row:
            return self._norm_industrial(row)
        if "_date" in row:
            return self._norm_baidu(row)
        if "买报价" in row:
            return self._norm_fx(row)
        return {"raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_shipping(self, row):
        return {"date_str": str(row.get("日期", "")), "index_type": str(row.get("_index_type", "")),
                "value": self._sf(row.get("最新值")), "change_pct": self._sf(row.get("涨跌幅")),
                "chg_3m": self._sf(row.get("近3月涨跌幅")), "chg_6m": self._sf(row.get("近6月涨跌幅")),
                "chg_1y": self._sf(row.get("近1年涨跌幅")), "chg_2y": self._sf(row.get("近2年涨跌幅")),
                "chg_3y": self._sf(row.get("近3年涨跌幅")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_price(self, row):
        return {"date_str": str(row.get("日期", "")), "value": self._sf(row.get("最新值")),
                "change_pct": self._sf(row.get("涨跌幅")), "chg_3m": self._sf(row.get("近3月涨跌幅")),
                "chg_6m": self._sf(row.get("近6月涨跌幅")), "chg_1y": self._sf(row.get("近1年涨跌幅")),
                "chg_2y": self._sf(row.get("近2年涨跌幅")), "chg_3y": self._sf(row.get("近3年涨跌幅")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_yield(self, row):
        return {"term": str(row.get("term", "")), "cn_label": row.get("cnLabel"),
                "en_label": row.get("enLabel"), "yield_value": self._sf(row.get("value")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_repo(self, row):
        return {"date_str": str(row.get("date", "")), "fr001": self._sf(row.get("FR001")),
                "fr007": self._sf(row.get("FR007")), "fr014": self._sf(row.get("FR014")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_industrial(self, row):
        return {"item": str(row.get("商品", "")), "date_str": str(row.get("日期", "")),
                "value": self._sf(row.get("今值")), "forecast": self._sf(row.get("预测值")),
                "previous": self._sf(row.get("前值")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_baidu(self, row):
        name = str(row.get("名称/代码", ""))
        return {"date_str": str(row.get("_date", "")), "name": name,
                "change_pct": self._sf(row.get("涨跌幅")), "heat": self._sf(row.get("综合热度")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_fx(self, row):
        return {"pair": str(row.get("货币对", "")), "bid": self._sf(row.get("买报价")),
                "ask": self._sf(row.get("卖报价")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    def _norm_us(self, row):
        return {"symbol": str(row.get("_symbol", "")), "trade_date": str(row.get("日期", "")),
                "open": self._sf(row.get("开盘")), "high": self._sf(row.get("最高")),
                "low": self._sf(row.get("最低")), "close": self._sf(row.get("收盘")),
                "volume": self._sf(row.get("成交量")), "amount": self._sf(row.get("成交额")),
                "amplitude": self._sf(row.get("振幅")), "change_pct": self._sf(row.get("涨跌幅")),
                "change_amt": self._sf(row.get("涨跌额")), "turnover": self._sf(row.get("换手率")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str)}

    @staticmethod
    def _sf(val):
        try: return float(val) if val not in (None, "") else None
        except: return None

    # ── Store ──

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        if not records: return 0
        f = records[0]
        if "index_type" in f: return self._store_dedup(RawShippingIndex, records, ["date_str", "index_type"])
        if "chg_3m" in f and "index_type" not in f: return self._store_dedup(RawCommodityPrice, records, ["date_str"])
        if "yield_value" in f: return self._store_dedup(RawYieldCurve, records, ["term"])
        if "fr001" in f: return self._store_dedup(RawRepoRate, records, ["date_str"])
        if "forecast" in f: return self._store_dedup(RawIndustrialProduction, records, ["date_str", "item"])
        if "heat" in f: return self._store_dedup(RawBaiduHotSearch, records, ["date_str", "name"])
        if "bid" in f: return self._store_dedup(RawFxSpot, records, ["pair"])
        if "amplitude" in f: return self._store_dedup(RawUsStockDaily, records, ["symbol", "trade_date"])
        return 0
