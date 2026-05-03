"""宏观专题指标 — AkshareV11Collector.

9个API: 存款准备金/社消零售/用电/邮电/旅游外汇/民航客座/央行资产/保险/零售价格
"""

from __future__ import annotations
import json
from typing import Any
import pandas as pd
from src.models.akshare_v10 import RawMacroIndicator
from src.collectors.base import BaseAKShareCollector


class AkshareV11Collector(BaseAKShareCollector):
    """Batch 11: 存款准备金/社消/用电/邮电/旅游/民航/央行/保险/零售价格."""

    def __init__(self):
        super().__init__("akshare_v11")

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return []

    def validate(self, raw: list[dict]) -> list[dict]:
        return raw

    def store_raw(self, records: list) -> int:
        if not records:
            return 0
        return self._store_dedup(RawMacroIndicator, records, ["source", "date", "sub_key"])

    # ── 存款准备金率 ──
    def _fetch_rrr(self) -> list[dict]:
        df = self.ak.macro_china_reserve_requirement_ratio()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "reserve_ratio",
                "date": str(row["公布时间"])[:16],
                "sub_key": str(row.get("生效时间", ""))[:16],
                "value": float(row["大型金融机构-调整幅度"]) if not pd.isna(row.get("大型金融机构-调整幅度")) else None,
                "change_pct": float(row["消息公布次日指数涨跌-上证"]) if not pd.isna(row.get("消息公布次日指数涨跌-上证")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    # ── 社消零售总额 ──
    def _fetch_retail(self) -> list[dict]:
        df = self.ak.macro_china_consumer_goods_retail()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "retail_sales",
                "date": str(row["月份"])[:16],
                "sub_key": "",
                "value": float(row["当月"]) if not pd.isna(row.get("当月")) else None,
                "change_pct": float(row["同比增长"]) if not pd.isna(row.get("同比增长")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    # ── 全社会用电 ──
    def _fetch_electricity(self) -> list[dict]:
        df = self.ak.macro_china_society_electricity()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "electricity",
                "date": str(row["统计时间"])[:16],
                "sub_key": "",
                "value": float(row["全社会用电量"]) if not pd.isna(row.get("全社会用电量")) else None,
                "change_pct": float(row["全社会用电量同比"]) if not pd.isna(row.get("全社会用电量同比")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    # ── 邮电业务 ──
    def _fetch_postal(self) -> list[dict]:
        df = self.ak.macro_china_postal_telecommunicational()
        records = []
        for _, row in df.iterrows():
            v = row.get("邮电业务总量")
            records.append({
                "source": "postal_telecom",
                "date": str(row["统计时间"])[:16],
                "sub_key": "",
                "value": float(v) if v is not None and not pd.isna(v) else None,
                "change_pct": float(row["邮电业务总量同比增长"]) if not pd.isna(row.get("邮电业务总量同比增长")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    # ── 旅游外汇收入 ──
    def _fetch_tourism(self) -> list[dict]:
        df = self.ak.macro_china_international_tourism_fx()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "tourism_fx",
                "date": str(row["统计年度"])[:16],
                "sub_key": str(row.get("指标", "")),
                "value": float(row["数量"]) if not pd.isna(row.get("数量")) else None,
                "change_pct": float(row["比重"]) if not pd.isna(row.get("比重")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    # ── 民航客座率 ──
    def _fetch_aviation(self) -> list[dict]:
        df = self.ak.macro_china_passenger_load_factor()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "aviation_lf",
                "date": str(row["统计时间"])[:16],
                "sub_key": "",
                "value": float(row["客座率"]) if not pd.isna(row.get("客座率")) else None,
                "change_pct": float(row["载运率"]) if not pd.isna(row.get("载运率")) else None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    # ── 央行资产负债表 ──
    def _fetch_cb_balance(self) -> list[dict]:
        df = self.ak.macro_china_central_bank_balance()
        records = []
        for _, row in df.iterrows():
            # store main balance sheet items as separate sub_keys
            for key in ["总资产", "总负债", "储备货币", "外汇"]:
                v = row.get(key)
                if v is not None and not pd.isna(v):
                    records.append({
                        "source": "cb_balance",
                        "date": str(row["统计时间"])[:16],
                        "sub_key": key,
                        "value": float(v),
                        "change_pct": None,
                        "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
                    })
        return records

    # ── 保险业经营 ──
    def _fetch_insurance(self) -> list[dict]:
        df = self.ak.macro_china_insurance()
        records = []
        for _, row in df.iterrows():
            province = str(row.get("省市地区", ""))
            premium = row.get("原保险保费收入")
            if premium is not None and not pd.isna(premium):
                records.append({
                    "source": "insurance_op",
                    "date": str(row["统计时间"])[:16],
                    "sub_key": province,
                    "value": float(premium),
                    "change_pct": None,
                    "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
                })
        return records

    # ── 商品零售价格 ──
    def _fetch_rpi(self) -> list[dict]:
        df = self.ak.macro_china_retail_price_index()
        records = []
        for _, row in df.iterrows():
            records.append({
                "source": "retail_price_idx",
                "date": str(row["统计月份"])[:16],
                "sub_key": str(row.get("居民消费项目", "")),
                "value": float(row["零售商品价格指数"]) if not pd.isna(row.get("零售商品价格指数")) else None,
                "change_pct": None,
                "raw_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
            })
        return records

    def run(self, **kwargs) -> int:
        total = 0
        fetchers = [
            ("存款准备金",   self._fetch_rrr),
            ("社消零售",     self._fetch_retail),
            ("全社会用电",   self._fetch_electricity),
            ("邮电业务",     self._fetch_postal),
            ("旅游外汇",     self._fetch_tourism),
            ("民航客座率",   self._fetch_aviation),
            ("央行资产负债", self._fetch_cb_balance),
            ("保险业经营",   self._fetch_insurance),
            ("商品零售价格", self._fetch_rpi),
        ]
        for name, fetcher in fetchers:
            try:
                records = fetcher()
                n = self.store_raw(records)
                print(f"  {name}: {n} rows")
                total += n
            except Exception as e:
                print(f"  {name}: SKIP ({e})")
        print(f"\nTotal: {total} rows")
        return total
