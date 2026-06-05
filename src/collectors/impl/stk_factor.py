"""股票因子 — StkFactorCollector

Tushare stk_factor API — OHLCV + 复权价 + 技术指标.
"""

from __future__ import annotations

import json
from datetime import datetime as dt
from typing import Any

from src.db.session import db_session
from src.models.market import RawStkFactor
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class StkFactorCollector(BaseTushareCollector):
    """股票因子 collector — OHLCV + 复权价 + 技术指标.

    API: pro.stk_factor(ts_code=..., trade_date=..., start_date=..., end_date=...)
    Fields: ts_code, trade_date, close, open, high, low, pre_close,
            change, pct_change, vol, amount, adj_factor,
            open_hfq, open_qfq, close_hfq, close_qfq, high_hfq, high_qfq,
            low_hfq, low_qfq, pre_close_hfq, pre_close_qfq,
            macd_dif, macd_dea, macd, kdj_k, kdj_d, kdj_j,
            rsi_6, rsi_12, rsi_24, boll_upper, boll_mid, boll_lower, cci
    """

    def __init__(self, token: str):
        super().__init__("stk_factor", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, str] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if trade_date:
            params["trade_date"] = trade_date
        if not params:
            params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("stk_factor", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "open": _f(row.get("open"), 0),
                "high": _f(row.get("high"), 0),
                "low": _f(row.get("low"), 0),
                "close": _f(row.get("close"), 0),
                "pre_close": _f(row.get("pre_close"), 0),
                "change": _f(row.get("change"), 0),
                "pct_chg": _f(row.get("pct_change"), 0),
                "vol": _f(row.get("vol"), 0),
                "amount": _f(row.get("amount"), 0),
                "adj_factor": _f(row.get("adj_factor")),
                "open_hfq": _f(row.get("open_hfq")),
                "open_qfq": _f(row.get("open_qfq")),
                "close_hfq": _f(row.get("close_hfq")),
                "close_qfq": _f(row.get("close_qfq")),
                "high_hfq": _f(row.get("high_hfq")),
                "high_qfq": _f(row.get("high_qfq")),
                "low_hfq": _f(row.get("low_hfq")),
                "low_qfq": _f(row.get("low_qfq")),
                "pre_close_hfq": _f(row.get("pre_close_hfq")),
                "pre_close_qfq": _f(row.get("pre_close_qfq")),
                "macd_dif": _f(row.get("macd_dif")),
                "macd_dea": _f(row.get("macd_dea")),
                "macd": _f(row.get("macd")),
                "kdj_k": _f(row.get("kdj_k")),
                "kdj_d": _f(row.get("kdj_d")),
                "kdj_j": _f(row.get("kdj_j")),
                "rsi_6": _f(row.get("rsi_6")),
                "rsi_12": _f(row.get("rsi_12")),
                "rsi_24": _f(row.get("rsi_24")),
                "boll_upper": _f(row.get("boll_upper")),
                "boll_mid": _f(row.get("boll_mid")),
                "boll_lower": _f(row.get("boll_lower")),
                "cci": _f(row.get("cci")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStkFactor, records, ["ts_code", "trade_date"])
