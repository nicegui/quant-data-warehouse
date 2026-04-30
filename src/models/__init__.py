"""SQLAlchemy ORM models — all tables auto-discovered by init_db.py."""
from src.models.base import Base, TimestampMixin
from src.models.asset import Asset
from src.models.market import (
    RawStockDaily, CuratedStockDailyAdj, RawDailyBasic,
    RawCryptoOhlcv, CuratedCryptoOhlcv, RawStkMins,
    RawStockWeekly, RawStockMonthly, RawStkFactor,
    RawStkHolderNumber,
)
from src.models.news import RawConsultation, RawMajorNews
from src.models.fundamental import RawFinancialReports, RawFinancialIndicators, RawExpress, RawBalanceSheet, RawCashFlow, RawForecast, RawStkHolderTrade, RawStkHolderTop
from src.models.reference import RefStockBasic, RefTradeCal, RefAdjFactor
from src.models.pipeline import PipelineLog
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList
from src.models.moneyflow import RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10, RawMarginDetail, RawMarginTotal, RawMoneyflowHsgt, RawGgtDaily
from src.models.index import RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail, RawIndexWeight, RefIndexBasic
from src.models.macro import RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply, RawShibor, RawCnPpi, RawSfMonth
from src.models.futures import RawFutDaily, RawFutHolding
from src.models.fund import RawFundDaily, RawFundPortfolio, RawFundBasic, RawFundNav
from src.models.corporate_action import RawSuspendD, RawDividend
from src.models.hk_market import RawHkDaily
from src.models.convertible_bond import RawCbDaily

__all__ = [
    "Base", "TimestampMixin",
    "Asset",
    "RawStockDaily", "CuratedStockDailyAdj", "RawDailyBasic",
    "RawCryptoOhlcv", "CuratedCryptoOhlcv", "RawStkMins",
    "RawStockWeekly", "RawStockMonthly", "RawStkFactor", "RawStkHolderNumber",
    "RawConsultation", "RawMajorNews",
    "RawFinancialReports", "RawFinancialIndicators",
    "RawExpress", "RawBalanceSheet", "RawCashFlow",
    "RefStockBasic", "RefTradeCal", "RefAdjFactor",
    "PipelineLog",
    "RawTopInst", "RawStkLimit", "RawLimitList", "RawTopList",
    "RawMoneyflow", "RawMoneyflowMktDc", "RawHsgtTop10", "RawGgtTop10", "RawMarginDetail", "RawMarginTotal", "RawMoneyflowHsgt", "RawGgtDaily",
    "RawIndexDaily", "RawSwDaily", "RefConcept", "RefConceptDetail", "RawIndexWeight", "RefIndexBasic",
    "RawCnCpi", "RawCnPmi", "RawCnGdp", "RawCnMoneySupply", "RawShibor", "RawCnPpi", "RawSfMonth",
    "RawFutDaily", "RawFutHolding",
    "RawFundDaily", "RawFundPortfolio", "RawFundBasic", "RawFundNav",
    "RawSuspendD", "RawDividend",
    "RawHkDaily", "RawCbDaily", "RawForecast", "RawStkHolderTrade", "RawStkHolderTop",
]
