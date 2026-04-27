"""Tushare Pro collectors — ALL important API interfaces.

Each collector follows the same pattern:
  __init__(name, token) -> fetch() -> validate() -> store_raw()
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from src.db.session import db_session
from src.models.market import RawStockDaily, CuratedStockDailyAdj, RawDailyBasic
from src.models.news import RawConsultation
from src.models.fundamental import RawFinancialReports, RawFinancialIndicators
from src.models.reference import RefAdjFactor, RefStockBasic, RefTradeCal
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList
from src.models.moneyflow import RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10, RawMarginDetail
from src.models.index import RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail
from src.models.macro import RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply, RawShibor
from src.models.futures import RawFutDaily, RawFutHolding
from src.models.fund import RawFundDaily, RawFundPortfolio
from src.collectors.base import BaseTushareCollector


class StockDailyCollector(BaseTushareCollector):
    """A-share daily OHLCV data collector.

    Fetches daily bars from Tushare, stores raw, then computes
    forward-adjusted (前复权) curated layer.
    """

    def __init__(self, token: str):
        super().__init__("stock_daily", token)

    def fetch(self, trade_date: Optional[str] = None, **kwargs) -> list[dict[str, Any]]:
        """Fetch daily data. If trade_date is None, fetches latest trading day."""
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call("daily", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Basic field normalization."""
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "pre_close": float(row.get("pre_close", 0)),
                "change": float(row.get("change", 0)),
                "pct_chg": float(row.get("pct_chg", 0)),
                "vol": float(row.get("vol", 0)),
                "amount": float(row.get("amount", 0)),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Append-only insert into raw_stock_daily with dedup."""
        written = 0
        with db_session() as session:
            for rec in records:
                # Dedup by (ts_code, trade_date)
                existing = session.query(RawStockDaily).filter(
                    RawStockDaily.ts_code == rec["ts_code"],
                    RawStockDaily.trade_date == rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStockDaily(**rec))
                written += 1
        return written

    def compute_curated(self, batch_size: int = 500) -> int:
        """Compute forward-adjusted (前复权) daily bars from raw layer.

        Formula: adj_price = raw_price * adj_factor
        where adj_factor = cumprod of split/dividend adjustment.
        """
        from src.models.reference import RefAdjFactor

        # Get all distinct stocks in raw
        with db_session() as session:
            ts_codes = [
                r[0] for r in session.query(RawStockDaily.ts_code).distinct().all()
            ]

        total_written = 0
        for ts_code in ts_codes:
            with db_session() as session:
                # Get adjustment factors for this stock
                factors = {
                    f.trade_date: f.adj_factor
                    for f in session.query(RefAdjFactor).filter(
                        RefAdjFactor.ts_code == ts_code
                    ).all()
                }

                if not factors:
                    continue

                # Get unprocessed raw data
                existing_dates = set(
                    r[0] for r in session.query(CuratedStockDailyAdj.trade_date).all()
                )

                raw_records = session.query(RawStockDaily).filter(
                    RawStockDaily.ts_code == ts_code,
                ).all()

                for raw in raw_records:
                    adj = factors.get(raw.trade_date)
                    if adj is None:
                        continue

                    if raw.trade_date in existing_dates:
                        continue

                    curated = CuratedStockDailyAdj(
                        trade_date=raw.trade_date,
                        open_adj=round(raw.open * adj, 4),
                        high_adj=round(raw.high * adj, 4),
                        low_adj=round(raw.low * adj, 4),
                        close_adj=round(raw.close * adj, 4),
                        volume=raw.vol,
                        amount=raw.amount,
                        adj_factor=adj,
                        valid_from=datetime.now(timezone.utc),
                        valid_to=None,
                        version=1,
                    )
                    session.add(curated)
                    total_written += 1

        return total_written


class ConsultationCollector(BaseTushareCollector):
    """Tushare news/consultation collector (每5分钟爬一次)."""

    def __init__(self, token: str):
        super().__init__("consultations", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch latest consultations."""
        src = kwargs.get("src", "sina")
        return self.api_call("news", src=src)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "news_id": str(row.get("id", "")),
                "title": row.get("title", ""),
                "content": row.get("content"),
                "source": row.get("source"),
                "pub_time": row.get("datetime"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Upsert by news_id."""
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawConsultation).filter(
                    RawConsultation.news_id == rec["news_id"]
                ).first()
                if existing:
                    continue
                session.add(RawConsultation(**rec))
                written += 1
        return written


class StockBasicCollector(BaseTushareCollector):
    """Stock master data (全量更新，每周一次)."""

    def __init__(self, token: str):
        super().__init__("stock_basic", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("stock_basic", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
                "area": row.get("area"),
                "industry": row.get("industry"),
                "market": row.get("market"),
                "list_date": row.get("list_date"),
                "delist_date": row.get("delist_date"),
                "is_hs": row.get("is_hs"),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        """Replace stock basic reference data."""
        written = 0
        with db_session() as session:
            # Clear and repopulate (this is reference data, small table)
            session.query(RefStockBasic).delete()
            for rec in records:
                session.add(RefStockBasic(**rec))
                written += 1
        return written


class FinancialReportCollector(BaseTushareCollector):
    """Financial reports collector."""

    def __init__(self, token: str):
        super().__init__("financial_reports", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("fina_mainbz_vip", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "revenue": self._safe_float(row.get("revenue")),
                "operating_profit": self._safe_float(row.get("operating_profit")),
                "net_profit": self._safe_float(row.get("net_profit")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialReports).filter(
                    RawFinancialReports.ts_code == rec["ts_code"],
                    RawFinancialReports.end_date == rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialReports(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class FinancialIndicatorCollector(BaseTushareCollector):
    """Financial indicators collector (ROE/EPS/PE/PB)."""

    def __init__(self, token: str):
        super().__init__("financial_indicators", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        return self.api_call("fina_indicator_vip", **kwargs)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "end_date": row.get("end_date"),
                "eps": self._safe_float(row.get("eps")),
                "roe": self._safe_float(row.get("roe")),
                "bps": self._safe_float(row.get("bps")),
                "pe": self._safe_float(row.get("pe")),
                "pb": self._safe_float(row.get("pb")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFinancialIndicators).filter(
                    RawFinancialIndicators.ts_code == rec["ts_code"],
                    RawFinancialIndicators.end_date == rec["end_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFinancialIndicators(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class AdjFactorCollector(BaseTushareCollector):
    """Forward adjustment factor collector."""

    def __init__(self, token: str):
        super().__init__("adj_factor", token)

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        params = {}
        start_date = kwargs.get("start_date", "20000101")
        trade_date = kwargs.get("trade_date")
        if trade_date:
            params["trade_date"] = trade_date
        else:
            params["start_date"] = start_date
        return self.api_call("adj_factor", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "adj_factor": float(row.get("adj_factor", 1)),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefAdjFactor).filter(
                    RefAdjFactor.ts_code == rec["ts_code"],
                    RefAdjFactor.trade_date == rec["trade_date"],
                ).first()
                if existing:
                    existing.adj_factor = rec["adj_factor"]
                else:
                    session.add(RefAdjFactor(**rec))
                written += 1
        return written


class TopInstCollector(BaseTushareCollector):
    """龙虎榜机构成交明细 — Tushare top_inst."""

    def __init__(self, token: str):
        super().__init__("top_inst", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict[str, Any]]:
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        else:
            # Default to latest trading day
            from datetime import datetime as dt
            params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("top_inst", **params)

    def validate(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "exalter": row.get("exalter"),
                "buy": self._safe_float(row.get("buy")) or 0,
                "buy_rate": self._safe_float(row.get("buy_rate")),
                "sell": self._safe_float(row.get("sell")) or 0,
                "sell_rate": self._safe_float(row.get("sell_rate")),
                "net_buy": self._safe_float(row.get("net_buy")) or 0,
                "side": row.get("side"),
                "reason": row.get("reason"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict[str, Any]]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawTopInst).filter(
                    RawTopInst.ts_code == rec["ts_code"],
                    RawTopInst.trade_date == rec["trade_date"],
                    RawTopInst.side == rec["side"],
                ).first()
                if existing:
                    continue
                session.add(RawTopInst(**rec))
                written += 1
        return written

    @staticmethod
    def _safe_float(v) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class DailyBasicCollector(BaseTushareCollector):
    """A-share daily basic indicators collector (PE/PB/换手率/市值)."""

    def __init__(self, token: str):
        super().__init__("daily_basic", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt
        params = {}
        if trade_date:
            params["trade_date"] = trade_date
        else:
            params["trade_date"] = dt.now().strftime("%Y%m%d")
        return self.api_call("daily_basic", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "close": _f(row.get("close")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "pre_close": _f(row.get("pre_close")) or 0,
                "change": _f(row.get("change")) or 0,
                "pct_chg": _f(row.get("pct_chg")) or 0,
                "vol": _f(row.get("vol")) or 0,
                "amount": _f(row.get("amount")) or 0,
                "turnover_rate": _f(row.get("turnover_rate")),
                "turnover_rate_f": _f(row.get("turnover_rate_f")),
                "pe": _f(row.get("pe")),
                "pe_ttm": _f(row.get("pe_ttm")),
                "pb": _f(row.get("pb")),
                "ps": _f(row.get("ps")),
                "ps_ttm": _f(row.get("ps_ttm")),
                "dv_ratio": _f(row.get("dv_ratio")),
                "dv_ttm": _f(row.get("dv_ttm")),
                "total_mv": _f(row.get("total_mv")),
                "circ_mv": _f(row.get("circ_mv")),
                "total_share": _f(row.get("total_share")),
                "float_share": _f(row.get("float_share")),
                "free_share": _f(row.get("free_share")),
                "avg_price": _f(row.get("avg_price")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        from src.models.market import RawDailyBasic
        from src.db.session import db_session
        from sqlalchemy import and_
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawDailyBasic).filter(
                    and_(
                        RawDailyBasic.ts_code == rec["ts_code"],
                        RawDailyBasic.trade_date == rec["trade_date"],
                    )
                ).first()
                if existing:
                    continue
                session.add(RawDailyBasic(**rec))
                written += 1
        return written


class MoneyflowCollector(BaseTushareCollector):
    """资金流向 — moneyflow + moneyflow_mkt_dc + hsgt_top10 + ggt_top10 + margin_detail."""

    def __init__(self, token: str):
        super().__init__("moneyflow", token)

    def fetch_moneyflow(self, trade_date: str) -> list[dict]:
        return self.api_call("moneyflow", trade_date=trade_date)

    def store_moneyflow(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMoneyflow).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawMoneyflow(**rec))
                written += 1
        return written

    def fetch_hsgt_top10(self, trade_date: str) -> list[dict]:
        return self.api_call("hsgt_top10", trade_date=trade_date)

    def store_hsgt_top10(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawHsgtTop10).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawHsgtTop10(**rec))
                written += 1
        return written

    def fetch_ggt_top10(self, trade_date: str) -> list[dict]:
        return self.api_call("ggt_top10", trade_date=trade_date)

    def store_ggt_top10(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawGgtTop10).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawGgtTop10(**rec))
                written += 1
        return written

    def fetch_margin_detail(self, trade_date: str) -> list[dict]:
        return self.api_call("margin_detail", trade_date=trade_date)

    def store_margin_detail(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawMarginDetail).filter_by(
                    trade_date=rec["trade_date"],
                    ts_code=rec["ts_code"],
                ).first()
                if existing:
                    continue
                session.add(RawMarginDetail(**rec))
                written += 1
        return written


class StkLimitCollector(BaseTushareCollector):
    """涨跌停价格限制 — stk_limit."""

    def __init__(self, token: str):
        super().__init__("stk_limit", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt
        td = trade_date or dt.now().strftime("%Y%m%d")
        return self.api_call("stk_limit", trade_date=td)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": row.get("trade_date"),
                "ts_code": row.get("ts_code", ""),
                "pre_close": _f(row.get("pre_close")),
                "up_limit": _f(row.get("up_limit")),
                "down_limit": _f(row.get("down_limit")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawStkLimit).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawStkLimit(**rec))
                written += 1
        return written


class ConceptCollector(BaseTushareCollector):
    """概念板块 — concept + ths_member."""

    def __init__(self, token: str):
        super().__init__("concept", token)

    def fetch_concepts(self) -> list[dict]:
        """Fetch all concept categories."""
        return self.api_call("concept")

    def store_concepts(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RefConcept).filter_by(
                    code=rec["code"]
                ).first()
                if existing:
                    continue
                session.add(RefConcept(**rec))
                written += 1
        return written

    def fetch_ths_member(self, concept_code: str) -> list[dict]:
        return self.api_call("ths_member", ts_code=concept_code)


class IndexCollector(BaseTushareCollector):
    """指数日线 — index_daily + sw_daily."""

    def __init__(self, token: str):
        super().__init__("index_daily", token)

    def fetch_index(self, trade_date: str) -> list[dict]:
        return self.api_call("index_daily", trade_date=trade_date)

    def store_index(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawIndexDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawIndexDaily(**rec))
                written += 1
        return written

    def fetch_sw_daily(self, trade_date: str) -> list[dict]:
        return self.api_call("sw_daily", trade_date=trade_date)

    def store_sw_daily(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawSwDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawSwDaily(**rec))
                written += 1
        return written


class MacroCollector(BaseTushareCollector):
    """宏观经济 — cpi/pmi/gdp/m2/shibor."""

    def __init__(self, token: str):
        super().__init__("macro", token)

    def fetch_cpi(self) -> list[dict]:
        return self.api_call("cn_cpi")

    def store_cpi(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnCpi).filter_by(
                    month=rec["month"]
                ).first()
                if existing:
                    continue
                session.add(RawCnCpi(**rec))
                written += 1
        return written

    def fetch_pmi(self) -> list[dict]:
        return self.api_call("cn_pmi")

    def store_pmi(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnPmi).filter_by(
                    month=rec["month"]
                ).first()
                if existing:
                    continue
                session.add(RawCnPmi(**rec))
                written += 1
        return written

    def fetch_gdp(self) -> list[dict]:
        return self.api_call("cn_gdp")

    def store_gdp(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnGdp).filter_by(
                    quarter=rec["quarter"]
                ).first()
                if existing:
                    continue
                session.add(RawCnGdp(**rec))
                written += 1
        return written

    def fetch_money_supply(self) -> list[dict]:
        return self.api_call("cn_m")

    def store_money_supply(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawCnMoneySupply).filter_by(
                    month=rec["month"]
                ).first()
                if existing:
                    continue
                session.add(RawCnMoneySupply(**rec))
                written += 1
        return written

    def fetch_shibor(self) -> list[dict]:
        return self.api_call("shibor")

    def store_shibor(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawShibor).filter_by(
                    date=rec["date"]
                ).first()
                if existing:
                    continue
                session.add(RawShibor(**rec))
                written += 1
        return written


class FuturesCollector(BaseTushareCollector):
    """期货 — fut_daily + fut_holding."""

    def __init__(self, token: str):
        super().__init__("futures", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt
        td = trade_date or dt.now().strftime("%Y%m%d")
        return self.api_call("fut_daily", trade_date=td)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "pre_close": _f(row.get("pre_close")),
                "pre_settle": _f(row.get("pre_settle")),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "close": _f(row.get("close")),
                "settle": _f(row.get("settle")),
                "change1": _f(row.get("change1")),
                "change2": _f(row.get("change2")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
                "oi": _f(row.get("oi")),
                "oi_chg": _f(row.get("oi_chg")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFutDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFutDaily(**rec))
                written += 1
        return written


class FundCollector(BaseTushareCollector):
    """基金/ETF — fund_daily + fund_portfolio."""

    def __init__(self, token: str):
        super().__init__("fund", token)

    def fetch(self, trade_date: str = "", **kwargs) -> list[dict]:
        from datetime import datetime as dt
        td = trade_date or dt.now().strftime("%Y%m%d")
        return self.api_call("fund_daily", trade_date=td)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": row.get("trade_date"),
                "open": _f(row.get("open")),
                "high": _f(row.get("high")),
                "low": _f(row.get("low")),
                "close": _f(row.get("close")),
                "pre_close": _f(row.get("pre_close")),
                "change": _f(row.get("change")),
                "pct_chg": _f(row.get("pct_chg")),
                "vol": _f(row.get("vol")),
                "amount": _f(row.get("amount")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        written = 0
        with db_session() as session:
            for rec in records:
                existing = session.query(RawFundDaily).filter_by(
                    ts_code=rec["ts_code"],
                    trade_date=rec["trade_date"],
                ).first()
                if existing:
                    continue
                session.add(RawFundDaily(**rec))
                written += 1
        return written


def _f(v):
    """Safe float conversion."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None
