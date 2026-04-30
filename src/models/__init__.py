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
    RawRepurchase, RawPledgeStat,
)
from src.models.reference import RefStockBasic, RefTradeCal, RefAdjFactor, RawNewShare, RawNameChange
from src.models.pipeline import PipelineLog
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList
from src.models.moneyflow import (
    RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10,
    RawMarginDetail, RawMarginTotal, RawMoneyflowHsgt, RawGgtDaily,
)
from src.models.index import (
    RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail,
    RawIndexWeight, RefIndexBasic,
)
from src.models.macro import (
    RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply,
    RawShibor, RawCnPpi, RawSfMonth, RawYieldCurve,
)
from src.models.futures import RawFutDaily, RawFutHolding, RefFutBasic, RawFutWsr
from src.models.fund import RawFundDaily, RawFundPortfolio, RawFundBasic, RawFundNav
from src.models.corporate_action import RawSuspendD, RawDividend
from src.models.hk_market import RawHkDaily
from src.models.convertible_bond import RawCbDaily
from src.models.us_market import RawUsDaily, RawUsBasic
from src.models.bond import RawBondDaily
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
    "RefStockBasic", "RefTradeCal", "RefAdjFactor", "RawNewShare", "RawNameChange",
    "PipelineLog",
    "RawTopInst", "RawStkLimit", "RawLimitList", "RawTopList",
    "RawMoneyflow", "RawMoneyflowMktDc", "RawHsgtTop10", "RawGgtTop10", "RawMarginDetail", "RawMarginTotal", "RawMoneyflowHsgt", "RawGgtDaily",
    "RawIndexDaily", "RawSwDaily", "RefConcept", "RefConceptDetail", "RawIndexWeight", "RefIndexBasic",
    "RawCnCpi", "RawCnPmi", "RawCnGdp", "RawCnMoneySupply", "RawShibor", "RawCnPpi", "RawSfMonth", "RawYieldCurve",
    "RawFutDaily", "RawFutHolding", "RefFutBasic", "RawFutWsr",
    "RawFundDaily", "RawFundPortfolio", "RawFundBasic", "RawFundNav",
    "RawSuspendD", "RawDividend",
    "RawHkDaily", "RawCbDaily", "RawForecast", "RawStkHolderTrade", "RawStkHolderTop",
    "RawFinaAudit", "RawFinaMainbz", "RawRepurchase", "RawPledgeStat",
    "RawUsDaily", "RawUsBasic", "RawBondDaily",
    "RawThsDaily", "RawThsHot",
]
