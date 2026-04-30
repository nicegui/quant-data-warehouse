"""Collector implementations — one file per data source."""

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
from src.collectors.impl.margin import MarginCollector

# ── NEW collectors (2026-04-30) ──
from src.collectors.impl.stk_mins import StkMinsCollector
from src.collectors.impl.major_news import MajorNewsCollector
from src.collectors.impl.trade_cal import TradeCalCollector
from src.collectors.impl.limit_list import LimitListCollector
from src.collectors.impl.top_list import TopListCollector
from src.collectors.impl.suspend_d import SuspendDCollector
from src.collectors.impl.dividend import DividendCollector
from src.collectors.impl.express import ExpressCollector
from src.collectors.impl.balance_sheet import BalanceSheetCollector
from src.collectors.impl.cash_flow import CashFlowCollector
from src.collectors.impl.hk_daily import HkDailyCollector
from src.collectors.impl.cb_daily import CbDailyCollector
from src.collectors.impl.forecast import ForecastCollector
from src.collectors.impl.weekly_monthly import WeeklyMonthlyCollector
from src.collectors.impl.margin_total import MarginTotalCollector
from src.collectors.impl.stk_factor import StkFactorCollector

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
    "MarginCollector",
    # NEW
    "StkMinsCollector",
    "MajorNewsCollector",
    "TradeCalCollector",
    "LimitListCollector",
    "TopListCollector",
    "SuspendDCollector",
    "DividendCollector",
    "ExpressCollector",
    "BalanceSheetCollector",
    "CashFlowCollector",
    "HkDailyCollector",
    "CbDailyCollector",
    "ForecastCollector",
    "WeeklyMonthlyCollector",
    "MarginTotalCollector",
    "StkFactorCollector",
]
