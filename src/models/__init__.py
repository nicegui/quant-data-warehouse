"""SQLAlchemy ORM models — all tables auto-discovered by init_db.py."""
from src.models.base import Base, TimestampMixin
from src.models.asset import Asset
from src.models.market import (
    RawStockDaily, CuratedStockDailyAdj, RawDailyBasic,
    RawCryptoOhlcv, CuratedCryptoOhlcv, RawStkMins,
    RawStockWeekly, RawStockMonthly, RawStkFactor,
    RawStkHolderNumber, RawBlockTrade, RawStkAccount, RawShareFloat,
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
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList, RawCyqChips, RawCyqPerf
from src.models.moneyflow import (
    RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10,
    RawMarginDetail, RawMarginTotal, RawMoneyflowHsgt, RawGgtDaily, RawGgtMonthly, RefHsConst,
    RawMarginSecs,
)
from src.models.index import (
    RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail,
    RawIndexWeight, RefIndexBasic, RefIndexClassify,
)
from src.models.dc_index import RawDcIndex
from src.models.macro import (
    RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply,
    RawShibor, RawCnPpi, RawSfMonth, RawYieldCurve,
)
from src.models.futures import RawFutDaily, RawFutHolding, RefFutBasic, RawFutWsr, RawFutMapping, RawFutSettle
from src.models.fund import RawFundDaily, RawFundPortfolio, RawFundBasic, RawFundNav, RawFundAdj, RawFundDiv, RawFundShare, RawFundManager
from src.models.corporate_action import RawSuspendD, RawDividend, RawSuspend
from src.models.hk_market import RawHkDaily, RefHkBasic, RawHkMins
from src.models.convertible_bond import RawCbDaily, RefCbBasic, RawCbIssue, RawCbRate
from src.models.us_market import RawUsDaily, RawUsBasic, RefUsTradeCal
from src.models.fx_market import RawFxDaily, RefFxBasic
from src.models.opt_market import RefOptBasic, RawOptDaily
from src.models.rate import RawShiborLpr, RawShiborQuote, RawLibor, RawHibor, RawWzIndex
from src.models.events import RawEcoCal, RefBrokerRecommend
from src.models.bond import RawBondDaily, RawYcCb, RawBondBlk
from src.models.ths import RawThsDaily, RawThsHot
from src.models.akshare_macro import (
    RawAkshareCpi, RawAksharePmi, RawAkshareGdp,
    RawAkshareMoneySupply, RawAkshareHsgtHist,
)
from src.models.baostock import RefBaostockBasic

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
    "RawTopInst", "RawStkLimit", "RawLimitList", "RawTopList", "RawCyqChips", "RawCyqPerf",
    "RawMoneyflow", "RawMoneyflowMktDc", "RawHsgtTop10", "RawGgtTop10", "RawMarginDetail", "RawMarginTotal", "RawMoneyflowHsgt", "RawGgtDaily",
    "RawIndexDaily", "RawSwDaily", "RefConcept", "RefConceptDetail", "RawIndexWeight", "RefIndexBasic", "RefIndexClassify",
    "RawCnCpi", "RawCnPmi", "RawCnGdp", "RawCnMoneySupply", "RawShibor", "RawCnPpi", "RawSfMonth", "RawYieldCurve",
    "RawFutDaily", "RawFutHolding", "RefFutBasic", "RawFutWsr", "RawFutMapping", "RawFutSettle",
    "RawFundDaily", "RawFundPortfolio", "RawFundBasic", "RawFundNav", "RawFundAdj", "RawFundDiv", "RawFundShare",
    "RawSuspendD", "RawDividend", "RawSuspend",
    "RawHkDaily", "RefHkBasic", "RawHkMins", "RawCbDaily", "RawForecast", "RawStkHolderTrade", "RawStkHolderTop",
    "RawFinaAudit", "RawFinaMainbz", "RawRepurchase", "RawPledgeStat",
    "RawPledgeDetail", "RawStkHolderFloatTop",
    "RawUsDaily", "RawUsBasic", "RefUsTradeCal", "RawBondDaily", "RawBondBlk",
    "RawThsDaily", "RawThsHot",
    "RefCbBasic", "RawCbIssue", "RawCbRate", "RawYcCb",
    "RawFxDaily", "RefFxBasic", "RefOptBasic", "RawOptDaily",
    "RawShiborLpr", "RawShiborQuote", "RawLibor", "RawHibor", "RawWzIndex",
    "RawEcoCal", "RefBrokerRecommend",
    "RawStkSurv", "RawStkManagers", "RawStkRewards", "RawFundManager",
    "RawGgtMonthly", "RefHsConst",
    "RawDcIndex", "RawMarginSecs", "RawBakBasic",
    "RawAkshareCpi", "RawAksharePmi", "RawAkshareGdp",
    "RawAkshareMoneySupply", "RawAkshareHsgtHist",
    "RefBaostockBasic",
]
