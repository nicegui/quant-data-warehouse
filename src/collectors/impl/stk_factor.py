"""股票因子 — StkFactorCollector

Tushare stk_factor API — OHLCV + 估值/换手率/市值等.
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
    """股票因子 collector — OHLCV + 估值指标 + 换手率 + 市值.

    API: pro.stk_factor(ts_code=...)
    Fields: ts_code, trade_date, open, high, low, close, pre_close,
            change, pct_chg, vol, amount, adj_factor, turnover_rate,
            turnover_rate_f, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm,
            dv_ratio, dv_ttm, total_share, float_share, free_share,
            total_mv, circ_mv
    """

    def __init__(self, token: str):
        super().__init__("stk_factor", token)

    @property
    def checkpoint_key(self):
        return "trade_date"

    def fetch(self, trade_date: str = "", ts_code: str = "", **kwargs) -> list[dict]:
        td = trade_date or dt.now().strftime("%Y%m%d")
        params = {"trade_date": td}
        if ts_code:
            params["ts_code"] = ts_code
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
                "pct_chg": _f(row.get("pct_chg"), 0),
                "vol": _f(row.get("vol"), 0),
                "amount": _f(row.get("amount"), 0),
                "adj_factor": _f(row.get("adj_factor")),
                "turnover_rate": _f(row.get("turnover_rate")),
                "turnover_rate_f": _f(row.get("turnover_rate_f")),
                "volume_ratio": _f(row.get("volume_ratio")),
                "pe": _f(row.get("pe")),
                "pe_ttm": _f(row.get("pe_ttm")),
                "pb": _f(row.get("pb")),
                "ps": _f(row.get("ps")),
                "ps_ttm": _f(row.get("ps_ttm")),
                "dv_ratio": _f(row.get("dv_ratio")),
                "dv_ttm": _f(row.get("dv_ttm")),
                "total_share": _f(row.get("total_share")),
                "float_share": _f(row.get("float_share")),
                "free_share": _f(row.get("free_share")),
                "total_mv": _f(row.get("total_mv")),
                "circ_mv": _f(row.get("circ_mv")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkFactor).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkFactor(**rec))
                written += 1
        return written
