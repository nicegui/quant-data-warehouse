"""SQLAlchemy ORM models — all tables auto-discovered by init_db.py."""
from src.models.base import Base, TimestampMixin
from src.models.asset import Asset
from src.models.market import (
    RawStockDaily, CuratedStockDailyAdj, RawDailyBasic,
    RawCryptoOhlcv, CuratedCryptoOhlcv,
)
from src.models.news import RawConsultation, RawMajorNews
from src.models.fundamental import RawFinancialReports, RawFinancialIndicators
from src.models.reference import RefStockBasic, RefTradeCal, RefAdjFactor
from src.models.pipeline import PipelineLog
from src.models.sentiment import RawTopInst, RawStkLimit, RawLimitList, RawTopList
from src.models.moneyflow import RawMoneyflow, RawMoneyflowMktDc, RawHsgtTop10, RawGgtTop10, RawMarginDetail
from src.models.index import RawIndexDaily, RawSwDaily, RefConcept, RefConceptDetail
from src.models.macro import RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply, RawShibor
from src.models.futures import RawFutDaily, RawFutHolding
from src.models.fund import RawFundDaily, RawFundPortfolio

__all__ = [
    "Base", "TimestampMixin",
    "Asset",
    "RawStockDaily", "CuratedStockDailyAdj", "RawDailyBasic",
    "RawCryptoOhlcv", "CuratedCryptoOhlcv",
    "RawConsultation", "RawMajorNews",
    "RawFinancialReports", "RawFinancialIndicators",
    "RefStockBasic", "RefTradeCal", "RefAdjFactor",
    "PipelineLog",
    "RawTopInst", "RawStkLimit", "RawLimitList", "RawTopList",
    "RawMoneyflow", "RawMoneyflowMktDc", "RawHsgtTop10", "RawGgtTop10", "RawMarginDetail",
    "RawIndexDaily", "RawSwDaily", "RefConcept", "RefConceptDetail",
    "RawCnCpi", "RawCnPmi", "RawCnGdp", "RawCnMoneySupply", "RawShibor",
    "RawFutDaily", "RawFutHolding",
    "RawFundDaily", "RawFundPortfolio",
]
