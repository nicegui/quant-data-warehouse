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

# ── NEW collectors (2026-04-30) ──
from src.collectors.impl.stk_mins import StkMinsCollector
from src.collectors.impl.major_news import MajorNewsCollector
from src.collectors.impl.trade_cal import TradeCalCollector
from src.collectors.impl.limit_list import LimitListCollector
from src.collectors.impl.limit_list_ths import LimitListThsCollector
from src.collectors.impl.limit_list_d import LimitListDCollector
from src.collectors.impl.limit_step import LimitStepCollector
from src.collectors.impl.limit_cpt_list import LimitCptListCollector
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

# ── 基本面积木 (2026-04-30) ──
from src.collectors.impl.holder_number import StkHolderNumberCollector
from src.collectors.impl.holder import HolderCollector
from src.collectors.impl.moneyflow_hsgt import MoneyflowHsgtCollector
from src.collectors.impl.fund_basic import FundBasicCollector
from src.collectors.impl.fund_nav import FundNavCollector
from src.collectors.impl.index_basic import IndexBasicCollector
from src.collectors.impl.ggt_daily import GgtDailyCollector
from src.collectors.impl.cn_ppi import CnPpiCollector
from src.collectors.impl.sf_month import SfMonthCollector

# ── 锦上添花 (2026-04-30) ──
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

# ── 高优补缺 (2026-04-30) ──
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
from src.collectors.impl.ths_member import ThsMemberCollector
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
from src.collectors.impl.dc_member import DcMemberCollector
from src.collectors.impl.dc_daily import DcDailyCollector
from src.collectors.impl.dc_hot import DcHotCollector
from src.collectors.impl.hm_list import HmListCollector
from src.collectors.impl.hm_detail import HmDetailCollector
from src.collectors.impl.margin_secs import MarginSecsCollector
from src.collectors.impl.bak_basic import BakBasicCollector
from src.collectors.impl.moneyflow_ths import MoneyflowThsCollector
from src.collectors.impl.moneyflow_dc import MoneyflowDcCollector
from src.collectors.impl.moneyflow_cnt_ths import MoneyflowCntThsCollector
from src.collectors.impl.moneyflow_ind_ths import MoneyflowIndThsCollector
from src.collectors.impl.moneyflow_ind_dc import MoneyflowIndDcCollector
from src.collectors.impl.index_member import IndexMemberCollector
from src.collectors.impl.ci_index_member import CiIndexMemberCollector
from src.collectors.impl.ci_daily import CiDailyCollector
from src.collectors.impl.idx_factor_pro import IdxFactorProCollector
from src.collectors.impl.daily_info import DailyInfoCollector
from src.collectors.impl.research_report import ResearchReportCollector
from src.collectors.impl.kpl_list import KplListCollector
from src.collectors.impl.kpl_concept import KplConceptCollector
from src.collectors.impl.dc_concept import DcConceptCollector
from src.collectors.impl.dc_concept_cons import DcConceptConsCollector
from src.collectors.impl.qvix import QvixCollector, EpuCollector
from src.collectors.impl.social_finance import SocialFinanceCollector
from src.collectors.impl.fund_position import FundPositionCollector
from src.collectors.impl.fund_portfolio import FundPortfolioCollector
from src.collectors.impl.analyst_forecast import AnalystForecastCollector

# ── Non-Tushare collectors (2026-05-01) ──
from src.collectors.impl.akshare_macro import AkshareMacroCollector
from src.collectors.impl.akshare_hsgt import AkshareHsgtCollector
from src.collectors.impl.baostock_basic import BaostockBasicCollector


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
    # NEW (2026-04-30)
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
    # 基本面积木
    "StkHolderNumberCollector",
    "HolderCollector",
    "MoneyflowHsgtCollector",
    "FundBasicCollector",
    "FundNavCollector",
    "IndexBasicCollector",
    "GgtDailyCollector",
    "CnPpiCollector",
    "SfMonthCollector",
    # 锦上添花
    "RepurchaseCollector",
    "PledgeStatCollector",
    "FutBasicCollector",
    "FutWsrCollector",
    "StkAccountCollector",
    "ShareFloatCollector",
    "NameChangeCollector",
    "CctvNewsCollector",
    "ThsCollector", "BlockTradeCollector", "NewShareCollector",
    "FinaAuditCollector", "FinaMainbzCollector", "UsStockCollector",
    # 高优补缺
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
    "LimitListAllCollector",
    "LimitListThsCollector",
    "LimitListDCollector",
    "LimitStepCollector",
    "LimitCptListCollector", "IndexMonthlyCollector", "IndexWeeklyCollector",
    "ThsDailyCollector", "ThsMemberCollector", "ThsIndexCollector",
    "OptBasicCollector", "OptDailyCollector",
    "FxDailyCollector", "FxBasicCollector",
    "RepoDailyCollector", "BondBlkCollector",
    "StkSurvCollector", "StkManagersCollector", "StkRewardsCollector",
    "BrokerRecommendCollector", "FundManagerCollector",
    "HsConstCollector", "GgtMonthlyCollector",
    "HkBasicCollector", "HkMinsCollector", "UsTradeCalCollector",
    "ShiborLprCollector", "ShiborQuoteCollector", "LiborCollector",
    "HiborCollector", "WzIndexCollector", "EcoCalCollector",
    # 筹码分布
    "CyqChipsCollector", "CyqPerfCollector",
    # dc_index / margin_secs / bak_basic
    "DcIndexCollector", "DcMemberCollector", "DcDailyCollector", "DcHotCollector", "HmListCollector", "HmDetailCollector", "MarginSecsCollector", "BakBasicCollector",
    "MoneyflowThsCollector",
    "MoneyflowDcCollector",
    "MoneyflowCntThsCollector",
    "MoneyflowIndThsCollector",
    "MoneyflowIndDcCollector",
    # 开盘啦榜单
    "IndexMemberCollector",
    "CiIndexMemberCollector",
    "CiDailyCollector",
    "IdxFactorProCollector",
    "DailyInfoCollector",
    "ResearchReportCollector",
    "KplListCollector",
    "KplConceptCollector",
    "DcConceptCollector",
    "DcConceptConsCollector",
    # Non-Tushare collectors (akshare / baostock)
    "AkshareMacroCollector", "AkshareHsgtCollector", "BaostockBasicCollector",
    "QvixCollector", "EpuCollector", "SocialFinanceCollector",
    "AnalystForecastCollector", "FundPositionCollector", "FundPortfolioCollector",
]
