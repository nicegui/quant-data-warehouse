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
from src.collectors.impl.margin import MarginCollector
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
from src.collectors.impl.holder_number import StkHolderNumberCollector
from src.collectors.impl.holder import HolderCollector
from src.collectors.impl.moneyflow_hsgt import MoneyflowHsgtCollector
from src.collectors.impl.fund_basic import FundBasicCollector
from src.collectors.impl.fund_nav import FundNavCollector
from src.collectors.impl.index_basic import IndexBasicCollector
from src.collectors.impl.ggt_daily import GgtDailyCollector
from src.collectors.impl.cn_ppi import CnPpiCollector
from src.collectors.impl.sf_month import SfMonthCollector
from src.collectors.impl.repurchase import RepurchaseCollector
from src.collectors.impl.pledge_stat import PledgeStatCollector
from src.collectors.impl.fut_basic import FutBasicCollector
from src.collectors.impl.fut_wsr import FutWsrCollector
from src.collectors.impl.stk_account import StkAccountCollector
from src.collectors.impl.share_float import ShareFloatCollector
from src.collectors.impl.namechange import NameChangeCollector
from src.collectors.impl.cctv_news import CctvNewsCollector
from src.collectors.impl.ths import ThsCollector
from src.collectors.impl.block_trade import BlockTradeCollector
from src.collectors.impl.new_share import NewShareCollector
from src.collectors.impl.fina_audit import FinaAuditCollector
from src.collectors.impl.fina_mainbz import FinaMainbzCollector
from src.collectors.impl.us_stock import UsStockCollector


__all__ = [
    "StockDailyCollector", "StockBasicCollector", "AdjFactorCollector",
    "DailyBasicCollector", "ConsultationCollector", "FinancialReportCollector",
    "FinancialIndicatorCollector", "TopInstCollector", "MoneyflowCollector",
    "StkLimitCollector", "ConceptCollector", "IndexCollector",
    "MacroCollector", "FuturesCollector", "FundCollector", "MarginCollector",
    "StkMinsCollector", "MajorNewsCollector", "TradeCalCollector",
    "LimitListCollector", "TopListCollector", "SuspendDCollector",
    "DividendCollector", "ExpressCollector", "BalanceSheetCollector",
    "CashFlowCollector", "HkDailyCollector", "CbDailyCollector",
    "ForecastCollector", "WeeklyMonthlyCollector", "MarginTotalCollector",
    "StkFactorCollector", "StkHolderNumberCollector", "HolderCollector",
    "MoneyflowHsgtCollector", "FundBasicCollector", "FundNavCollector",
    "IndexBasicCollector", "GgtDailyCollector", "CnPpiCollector",
    "SfMonthCollector", "RepurchaseCollector", "PledgeStatCollector",
    "FutBasicCollector", "FutWsrCollector", "StkAccountCollector",
    "ShareFloatCollector", "NameChangeCollector", "CctvNewsCollector",
    "ThsCollector", "BlockTradeCollector", "NewShareCollector",
    "FinaAuditCollector", "FinaMainbzCollector", "UsStockCollector",
]
