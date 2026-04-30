"""Tushare Pro collectors — backwards-compatible re-exports.

All collector classes have been moved to individual files under
src/collectors/impl/ for better maintainability. This module
re-exports them so that existing imports continue to work.

Migration: update imports from:
    from src.collectors.tushare_collector import StockDailyCollector
to:
    from src.collectors.impl.stock_daily import StockDailyCollector
"""

from __future__ import annotations

from src.collectors.impl.stock_daily import StockDailyCollector
from src.collectors.impl.stock_basic import StockBasicCollector
from src.collectors.impl.adj_factor import AdjFactorCollector
from src.collectors.impl.daily_basic import DailyBasicCollector
from src.collectors.impl.consultations import ConsultationCollector
from src.collectors.impl.financial_reports import FinancialReportCollector
from src.collectors.impl.financial_indicators import FinancialIndicatorCollector
from src.collectors.impl.top_inst import TopInstCollector
from src.collectors.impl.moneyflow import MoneyflowCollector
from src.collectors.impl.stk_limit import StkLimitCollector
from src.collectors.impl.concept import ConceptCollector
from src.collectors.impl.index_daily import IndexCollector
from src.collectors.impl.macro import MacroCollector
from src.collectors.impl.futures import FuturesCollector
from src.collectors.impl.fund import FundCollector


__all__ = [
    "StockDailyCollector",
    "StockBasicCollector",
    "AdjFactorCollector",
    "DailyBasicCollector",
    "ConsultationCollector",
    "FinancialReportCollector",
    "FinancialIndicatorCollector",
    "TopInstCollector",
    "MoneyflowCollector",
    "StkLimitCollector",
    "ConceptCollector",
    "IndexCollector",
    "MacroCollector",
    "FuturesCollector",
    "FundCollector",
]
