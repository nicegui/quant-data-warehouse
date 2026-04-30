"""SQLAlchemy ORM models — all tables auto-discovered by init_db.py."""
from src.models.base import Base, TimestampMixin
from src.models.asset import Asset
from src.models.market import (
    RawStockDaily, CuratedStockDailyAdj, RawDailyBasic,
    RawCryptoOhlcv, CuratedCryptoOhlcv, RawStkMins,
    RawStockWeekly, RawStockMonthly, RawStkFactor,
    RawStkHolderNumber, RawBlockTrade, RawStkAccount, RawShareFloat,
)
from src.models.news import RawConsultation, RawMajorNews, RawCctvNews
from src.models.fundamental import (
    RawFinancialReports, RawFinancialIndicators, RawExpress,
    RawBalanceSheet, RawCashFlow, RawForecast,
    RawStkHolderTrade, RawStkHolderTop, RawFinaAudit, RawFinaMainbz,
    RawRepurchase, RawPledgeStat, RawPledgeDetail, RawStkHolderFloatTop,
)
from src.models.reference import RefStockBasic, RefTradeCal, RefAdjFactor, RawNewShare, RawNameChange, RefDisclosureDate
from src.models.pipeline import PipelineLog
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList
from src.models.moneyflow import (
    RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10,
    RawMarginDetail, RawMarginTotal, RawMoneyflowHsgt, RawGgtDaily,
)
from src.models.index import (
    RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail,
    RawIndexWeight, RefIndexBasic, RefIndexClassify,
)
from src.models.macro import (
    RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply,
    RawShibor, RawCnPpi, RawSfMonth, RawYieldCurve,
)
from src.models.futures import RawFutDaily, RawFutHolding, RefFutBasic, RawFutWsr, RawFutMapping, RawFutSettle
from src.models.fund import RawFundDaily, RawFundPortfolio, RawFundBasic, RawFundNav, RawFundAdj, RawFundDiv, RawFundShare
from src.models.corporate_action import RawSuspendD, RawDividend, RawSuspend
from src.models.hk_market import RawHkDaily
from src.models.convertible_bond import RawCbDaily, RefCbBasic, RawCbIssue, RawCbRate
from src.models.us_market import RawUsDaily, RawUsBasic
from src.models.bond import RawBondDaily, RawYcCb
from src.models.ths import RawThsDaily, RawThsHot

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
    "RawTopInst", "RawStkLimit", "RawLimitList", "RawTopList",
    "RawMoneyflow", "RawMoneyflowMktDc", "RawHsgtTop10", "RawGgtTop10", "RawMarginDetail", "RawMarginTotal", "RawMoneyflowHsgt", "RawGgtDaily",
    "RawIndexDaily", "RawSwDaily", "RefConcept", "RefConceptDetail", "RawIndexWeight", "RefIndexBasic", "RefIndexClassify",
    "RawCnCpi", "RawCnPmi", "RawCnGdp", "RawCnMoneySupply", "RawShibor", "RawCnPpi", "RawSfMonth", "RawYieldCurve",
    "RawFutDaily", "RawFutHolding", "RefFutBasic", "RawFutWsr", "RawFutMapping", "RawFutSettle",
    "RawFundDaily", "RawFundPortfolio", "RawFundBasic", "RawFundNav", "RawFundAdj", "RawFundDiv", "RawFundShare",
    "RawSuspendD", "RawDividend", "RawSuspend",
    "RawHkDaily", "RawCbDaily", "RawForecast", "RawStkHolderTrade", "RawStkHolderTop",
    "RawFinaAudit", "RawFinaMainbz", "RawRepurchase", "RawPledgeStat",
    "RawPledgeDetail", "RawStkHolderFloatTop",
    "RawUsDaily", "RawUsBasic", "RawBondDaily",
    "RawThsDaily", "RawThsHot",
    "RefCbBasic", "RawCbIssue", "RawCbRate", "RawYcCb",
]
