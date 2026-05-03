"""SQLAlchemy ORM models — all tables auto-discovered by init_db.py."""
from src.models.base import Base, TimestampMixin
from src.models.asset import Asset
from src.models.market import (
    RawStockDaily, CuratedStockDailyAdj, RawDailyBasic,
    RawCryptoOhlcv, CuratedCryptoOhlcv, RawStkMins,
    RawStockWeekly, RawStockMonthly, RawStkFactor,
    RawStkHolderNumber, RawBlockTrade, RawStkAccount, RawShareFloat,
    RawBakDaily, RawStkAccountOld,
)
from src.models.news import RawConsultation, RawMajorNews, RawCctvNews, RawStkSurv
from src.models.fundamental import (
    RawFinancialReports, RawFinancialIndicators, RawExpress,
    RawBalanceSheet, RawCashFlow, RawForecast,
    RawStkHolderTrade, RawStkHolderTop, RawFinaAudit, RawFinaMainbz,
    RawRepurchase, RawPledgeStat, RawPledgeDetail, RawStkHolderFloatTop,
    RawStkManagers, RawStkRewards,
)
from src.models.reference import RefStockBasic, RefTradeCal, RefAdjFactor, RawNewShare, RawNameChange, RefDisclosureDate, RawBakBasic
from src.models.pipeline import PipelineLog
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList, RawCyqChips, RawCyqPerf, RawStkShock, RawStkHighShock, RawStkAlert, RawLimitListThs, RawLimitListD, RawLimitStep, RawLimitCptList
from src.models.stk_factor_pro import RawStkNineturn
from src.models.moneyflow import (
    RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10,
    RawMarginDetail, RawMarginTotal, RawMoneyflowHsgt, RawGgtDaily, RawGgtMonthly, RefHsConst,
    RawMarginSecs, RawMoneyflowThs, RawMoneyflowDc, RawMoneyflowCntThs, RawMoneyflowIndThs, RawMoneyflowIndDc,
)
from src.models.index import (
    RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail,
    RawIndexWeight, RefIndexBasic, RefIndexClassify, RawThsDaily,
)
from src.models.dc_index import RawDcIndex
from src.models.dc_member import RawDcMember
from src.models.dc_daily import RawDcDaily
from src.models.hm_list import RawHmList
from src.models.hm_detail import RawHmDetail
from src.models.dc_hot import RawDcHot
from src.models.index_member import RawIndexMember
from src.models.ci_index_member import RawCiIndexMember
from src.models.ci_daily import RawCiDaily
from src.models.idx_factor_pro import RawIdxFactorPro
from src.models.daily_info import RawDailyInfo
from src.models.research_report import RawResearchReport
from src.models.kpl_list import RawKplList
from src.models.kpl_concept import RawKplConcept, RawKplConceptCons
from src.models.dc_concept import RawDcConcept
from src.models.dc_concept_cons import RawDcConceptCons
from src.models.macro import (
    RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply,
    RawShibor, RawCnPpi, RawSfMonth, RawYieldCurve,
)
from src.models.futures import RawFutDaily, RawFutHolding, RefFutBasic, RawFutWsr, RawFutMapping, RawFutSettle
from src.models.fund import RawFundDaily, RawFundPortfolio, RawFundBasic, RawFundNav, RawFundAdj, RawFundDiv, RawFundShare, RawFundManager
from src.models.corporate_action import RawSuspendD, RawDividend, RawSuspend
from src.models.hk_market import RawHkDaily, RefHkBasic, RawHkMins, RawStkAhComparison
from src.models.convertible_bond import RawCbDaily, RefCbBasic, RawCbIssue, RawCbRate
from src.models.us_market import RawUsDaily, RawUsBasic, RefUsTradeCal
from src.models.fx_market import RawFxDaily, RefFxBasic
from src.models.opt_market import RefOptBasic, RawOptDaily
from src.models.rate import RawShiborLpr, RawShiborQuote, RawLibor, RawHibor, RawWzIndex
from src.models.events import RawEcoCal, RefBrokerRecommend
from src.models.bond import RawBondDaily, RawYcCb, RawBondBlk
from src.models.ths import RawThsMember, RawThsHot
from src.models.akshare_macro import (
    RawAkshareCpi, RawAksharePmi, RawAkshareGdp,
    RawAkshareMoneySupply, RawAkshareHsgtHist,
)
from src.models.baostock import RefBaostockBasic
from src.models.hsgt_individual import RawHsgtIndividual
from src.models.cb_jsl import RawCbJsl
from src.models.fund_flow import RawFundFlow
from src.models.index_cons import RawIndexCons
from src.models.us_fundamental import (
    RawUsDividend, RawUsSplit, RawUsRecommendation,
    RawUsInstitutional, RawUsInfo,
)
from src.models.qvix import RawQvix, RawEpuIndex
from src.models.macro_fund import RawSocialFinance, RawFundPosition, RawFundHolding
from src.models.analyst import RawAnalystRank, RawAnalystDetail
from src.models.analyst_forecast import RawAnalystForecast
from src.models.foreign_futures import RawForeignFutures
from src.models.akshare_v2 import (
    RawRestrictedRelease, RawFxGold, RawConsumerGoods, RawRealEstate,
)
from src.models.akshare_v3 import (
    RawShippingIndex, RawCommodityPrice, RawYieldCurve,
    RawRepoRate, RawIndustrialProduction, RawBaiduHotSearch,
    RawFxSpot, RawUsStockDaily,
)
from src.models.akshare_v4 import (
    RawGlobalMacro, RawLprRate, RawCbIndex,
    RawHs300Option, RawEtfScale, RawUnemployment,
)
from src.models.akshare_v5 import (
    RawFundRating, RawFundManager, RawCreditSpread,
)
from src.models.akshare_v6 import RawIpoDeclare
from src.models.akshare_v7 import RawStockCxg

__all__ = [
    "Base", "TimestampMixin",
    "Asset",
    "RawStockDaily", "CuratedStockDailyAdj", "RawDailyBasic",
    "RawCryptoOhlcv", "CuratedCryptoOhlcv", "RawStkMins",
    "RawStockWeekly", "RawStockMonthly", "RawStkFactor", "RawStkHolderNumber",
    "RawBlockTrade", "RawStkAccount", "RawShareFloat",
    "RawConsultation", "RawMajorNews", "RawCctvNews",
    "RawFinancialReports", "RawFinancialIndicators",
    "RawExpress", "RawBalanceSheet", "RawCashFlow",
    "RefStockBasic", "RefTradeCal", "RefAdjFactor", "RawNewShare", "RawNameChange", "RefDisclosureDate",
    "PipelineLog",
    "RawTopInst", "RawStkLimit", "RawLimitList", "RawTopList", "RawCyqChips", "RawCyqPerf", "RawStkShock", "RawStkHighShock", "RawStkAlert",
    "RawLimitListThs",
    "RawLimitListD",
    "RawLimitStep",
    "RawLimitCptList",
    "RawMoneyflow", "RawMoneyflowMktDc", "RawHsgtTop10", "RawGgtTop10", "RawMarginDetail", "RawMarginTotal", "RawMoneyflowHsgt", "RawGgtDaily",
    "RawIndexDaily", "RawSwDaily", "RefConcept", "RefConceptDetail", "RawIndexWeight", "RefIndexBasic", "RefIndexClassify",
    "RawCnCpi", "RawCnPmi", "RawCnGdp", "RawCnMoneySupply", "RawShibor", "RawCnPpi", "RawSfMonth", "RawYieldCurve",
    "RawFutDaily", "RawFutHolding", "RefFutBasic", "RawFutWsr", "RawFutMapping", "RawFutSettle",
    "RawFundDaily", "RawFundPortfolio", "RawFundBasic", "RawFundNav", "RawFundAdj", "RawFundDiv", "RawFundShare",
    "RawSuspendD", "RawDividend", "RawSuspend",
    "RawHkDaily", "RefHkBasic", "RawHkMins", "RawStkAhComparison", "RawCbDaily", "RawForecast", "RawStkHolderTrade", "RawStkHolderTop",
    "RawFinaAudit", "RawFinaMainbz", "RawRepurchase", "RawPledgeStat",
    "RawPledgeDetail", "RawStkHolderFloatTop",
    "RawUsDaily", "RawUsBasic", "RefUsTradeCal", "RawBondDaily", "RawBondBlk",
    "RawThsMember", "RawThsHot",
    "RefCbBasic", "RawCbIssue", "RawCbRate", "RawYcCb",
    "RawFxDaily", "RefFxBasic", "RefOptBasic", "RawOptDaily",
    "RawShiborLpr", "RawShiborQuote", "RawLibor", "RawHibor", "RawWzIndex",
    "RawEcoCal", "RefBrokerRecommend",
    "RawStkSurv", "RawStkManagers", "RawStkRewards", "RawFundManager",
    "RawGgtMonthly", "RefHsConst",
    "RawDcIndex", "RawMarginSecs", "RawBakBasic",
    "RawDcMember", "RawDcDaily", "RawHmList", "RawHmDetail",
    "RawDcHot",
    "RawBakDaily", "RawStkAccountOld", "RawStkNineturn",
    "RawMoneyflowThs",
    "RawMoneyflowDc",
    "RawMoneyflowCntThs",
    "RawMoneyflowIndThs",
    "RawMoneyflowIndDc",
    "RawAkshareCpi", "RawAksharePmi", "RawAkshareGdp",
    "RawAkshareMoneySupply", "RawAkshareHsgtHist",
    "RefBaostockBasic",
    "RawCbJsl",
    "RawHsgtIndividual",
    "RawFundFlow",
    "RawIndexCons",
    "RawAnalystRank", "RawAnalystDetail",
    "RawUsDividend", "RawUsSplit", "RawUsRecommendation",
    "RawUsInstitutional", "RawUsInfo",
    "RawForeignFutures",
    "RawRestrictedRelease", "RawFxGold", "RawConsumerGoods", "RawRealEstate",
    "RawShippingIndex", "RawCommodityPrice", "RawYieldCurve",
    "RawRepoRate", "RawIndustrialProduction", "RawBaiduHotSearch",
    "RawFxSpot", "RawUsStockDaily",
    "RawGlobalMacro", "RawLprRate", "RawCbIndex",
    "RawHs300Option", "RawEtfScale", "RawUnemployment",
    "RawFundRating", "RawFundManager", "RawCreditSpread",
    "RawIpoDeclare",
    "RawStockCxg",
]
