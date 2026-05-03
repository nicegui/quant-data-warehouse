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
from src.collectors.impl.index_weight import IndexWeightCollector
from src.collectors.impl.index_classify import IndexClassifyCollector
from src.collectors.impl.margin_detail import MarginDetailCollector
from src.collectors.impl.pledge_detail import PledgeDetailCollector
from src.collectors.impl.stk_holdertrade import StkHolderTradeCollector
from src.collectors.impl.top10_holders import Top10HoldersCollector
from src.collectors.impl.top10_floatholders import Top10FloatHoldersCollector
from src.collectors.impl.suspend import SuspendCollector
from src.collectors.impl.disclosure_date import DisclosureDateCollector

# ── 中优补缺 (2026-04-30) ──
from src.collectors.impl.fut_holding import FutHoldingCollector
from src.collectors.impl.fut_mapping import FutMappingCollector
from src.collectors.impl.fut_settle import FutSettleCollector
from src.collectors.impl.fund_adj import FundAdjCollector
from src.collectors.impl.fund_div import FundDivCollector
from src.collectors.impl.fund_share import FundShareCollector
from src.collectors.impl.fund_portfolio import FundPortfolioCollector
from src.collectors.impl.cb_basic import CbBasicCollector
from src.collectors.impl.cb_issue import CbIssueCollector
from src.collectors.impl.cb_rate import CbRateCollector
from src.collectors.impl.yield_curve import YieldCurveCollector
from src.collectors.impl.stk_auction import StkAuctionCollector
from src.collectors.impl.index_dailybasic import IndexDailyBasicCollector
from src.collectors.impl.index_global import IndexGlobalCollector
from src.collectors.impl.limit_list_all import LimitListAllCollector
from src.collectors.impl.index_monthly import IndexMonthlyCollector
from src.collectors.impl.index_weekly import IndexWeeklyCollector
from src.collectors.impl.ths_daily import ThsDailyCollector
from src.collectors.impl.ths_index import ThsIndexCollector
from src.collectors.impl.opt_basic import OptBasicCollector
from src.collectors.impl.opt_daily import OptDailyCollector
from src.collectors.impl.fx_daily import FxDailyCollector
from src.collectors.impl.fx_obasic import FxBasicCollector
from src.collectors.impl.repo_daily import RepoDailyCollector
from src.collectors.impl.bond_blk import BondBlkCollector
from src.collectors.impl.stk_surv import StkSurvCollector
from src.collectors.impl.stk_managers import StkManagersCollector
from src.collectors.impl.stk_rewards import StkRewardsCollector
from src.collectors.impl.broker_recommend import BrokerRecommendCollector
from src.collectors.impl.fund_manager import FundManagerCollector
from src.collectors.impl.hs_const import HsConstCollector
from src.collectors.impl.ggt_monthly import GgtMonthlyCollector
from src.collectors.impl.income_vip import IncomeVipCollector
from src.collectors.impl.balance_sheet_vip import BalanceSheetVipCollector
from src.collectors.impl.cashflow_vip import CashFlowVipCollector
from src.collectors.impl.forecast_vip import ForecastVipCollector
from src.collectors.impl.fina_indicator_vip import FinaIndicatorVipCollector
from src.collectors.impl.fina_audit_vip import FinaAuditVipCollector
from src.collectors.impl.hk_basic import HkBasicCollector
from src.collectors.impl.hk_mins import HkMinsCollector
from src.collectors.impl.us_tradecal import UsTradeCalCollector
from src.collectors.impl.shibor_lpr import ShiborLprCollector
from src.collectors.impl.shibor_quote import ShiborQuoteCollector
from src.collectors.impl.libor import LiborCollector
from src.collectors.impl.hibor import HiborCollector
from src.collectors.impl.wz_index import WzIndexCollector
from src.collectors.impl.eco_cal import EcoCalCollector

# ── 筹码分布 (2026-05-01) ──
from src.collectors.impl.cyq_chips import CyqChipsCollector
from src.collectors.impl.cyq_perf import CyqPerfCollector

# ── dc_index / margin_secs / bak_basic (2026-05-01) ──
from src.collectors.impl.dc_index import DcIndexCollector
from src.collectors.impl.margin_secs import MarginSecsCollector
from src.collectors.impl.bak_basic import BakBasicCollector

# ── bak_daily / stk_account_old (2026-05-01) ──
from src.collectors.impl.bak_daily import BakDailyCollector
from src.collectors.impl.stk_account_old import StkAccountOldCollector

# ── stk_shock (2026-05-01) ──
from src.collectors.impl.stk_shock import StkShockCollector
from src.collectors.impl.stk_high_shock import StkHighShockCollector
from src.collectors.impl.stk_alert import StkAlertCollector

# ── report_rc (2026-05-01) ──
from src.collectors.impl.report_rc_vip import ReportRcVipCollector

# ── stk_factor_pro (2026-05-01) ──
from src.collectors.impl.stk_factor_pro import StkFactorProCollector

# ── ccass_hold (2026-05-01) ──
from src.collectors.impl.ccass_hold import CcassHoldCollector
from src.collectors.impl.ccass_hold_detail import CcassHoldDetailCollector

# ── hk_hold (2026-05-01) ──
from src.collectors.impl.hk_hold import HkHoldCollector

# ── yfinance / AKShare multi-source (2026-05-01) ──
from src.collectors.impl.us_fundamental import UsFundamentalCollector
from src.collectors.impl.cb_jsl import CbJslCollector
from src.collectors.impl.analyst import AnalystCollector
from src.collectors.impl.fund_flow import FundFlowCollector
from src.collectors.impl.index_cons import IndexConsCollector
from src.collectors.impl.hsgt_individual import HsgtIndividualCollector
from src.collectors.impl.foreign_futures import ForeignFuturesCollector

# ── Non-Tushare collectors (akshare / baostock) ──
from src.collectors.impl.akshare_macro import AkshareMacroCollector
from src.collectors.impl.akshare_hsgt import AkshareHsgtCollector
from src.collectors.impl.baostock_basic import BaostockBasicCollector
from src.collectors.impl.analyst_forecast import AnalystForecastCollector



__all__ = [
    "StockDailyCollector", "StockBasicCollector", "AdjFactorCollector",
    "DailyBasicCollector", "ConsultationCollector", "FinancialReportCollector",
    "FinancialIndicatorCollector", "TopInstCollector", "MoneyflowCollector",
    "StkLimitCollector", "ConceptCollector", "IndexCollector",
    "MacroCollector", "FuturesCollector", "FundCollector",
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
    "IndexWeightCollector", "IndexClassifyCollector",
    "MarginDetailCollector", "PledgeDetailCollector",
    "StkHolderTradeCollector", "Top10HoldersCollector",
    "Top10FloatHoldersCollector", "SuspendCollector",
    "DisclosureDateCollector",
    # 中优补缺
    "FutHoldingCollector", "FutMappingCollector", "FutSettleCollector",
    "FundAdjCollector", "FundDivCollector", "FundShareCollector",
    "FundPortfolioCollector", "CbBasicCollector", "CbIssueCollector",
    "CbRateCollector", "YieldCurveCollector",
    "StkAuctionCollector", "IndexDailyBasicCollector", "IndexGlobalCollector",
    "LimitListAllCollector", "IndexMonthlyCollector", "IndexWeeklyCollector",
    "ThsDailyCollector", "ThsIndexCollector",
    "OptBasicCollector", "OptDailyCollector",
    "FxDailyCollector", "FxBasicCollector",
    "RepoDailyCollector", "BondBlkCollector",
    "StkSurvCollector", "StkManagersCollector", "StkRewardsCollector",
    "BrokerRecommendCollector", "FundManagerCollector",
    "HsConstCollector", "GgtMonthlyCollector",
    "IncomeVipCollector",
    "BalanceSheetVipCollector",
    "CashFlowVipCollector",
    "ForecastVipCollector",
    "FinaIndicatorVipCollector",
    "FinaAuditVipCollector",
    "HkBasicCollector", "HkMinsCollector", "UsTradeCalCollector",
    "ShiborLprCollector", "ShiborQuoteCollector", "LiborCollector",
    "HiborCollector", "WzIndexCollector", "EcoCalCollector",
    # 筹码分布
    "CyqChipsCollector", "CyqPerfCollector",
    # dc_index / margin_secs / bak_basic
    "DcIndexCollector", "MarginSecsCollector", "BakBasicCollector",
    # bak_daily / stk_account_old
    "BakDailyCollector", "StkAccountOldCollector",
    # stk_shock
    "StkShockCollector", "StkHighShockCollector", "StkAlertCollector",
    # report_rc
    "ReportRcVipCollector",
    # stk_factor_pro
    "StkFactorProCollector",
    # ccass_hold
    "CcassHoldCollector", "CcassHoldDetailCollector",
    # hk_hold
    "HkHoldCollector",
    # yfinance / AKShare multi-source
    "UsFundamentalCollector", "CbJslCollector", "AnalystCollector",
    "FundFlowCollector",    "IndexConsCollector", "HsgtIndividualCollector", "ForeignFuturesCollector",
    # Non-Tushare collectors(akshare / baostock)
    "AkshareMacroCollector", "AkshareHsgtCollector", "BaostockBasicCollector",
    "AnalystForecastCollector",
]
