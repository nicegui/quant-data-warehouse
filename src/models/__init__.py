"""SQLAlchemy ORM models — all tables auto-discovered by init_db.py."""
from src.models.base import Base, TimestampMixin
from src.models.asset import Asset
from src.models.market import RawStockDaily, CuratedStockDailyAdj, RawCryptoOhlcv, CuratedCryptoOhlcv
from src.models.news import RawConsultation, RawMajorNews
from src.models.fundamental import RawFinancialReports, RawFinancialIndicators
from src.models.reference import RefStockBasic, RefTradeCal, RefAdjFactor
from src.models.pipeline import PipelineLog
from src.models.sentiment import RawTopInst, RawLimitList, RawTopList

__all__ = [
    "Base",
    "TimestampMixin",
    "Asset",
    "RawStockDaily",
    "CuratedStockDailyAdj",
    "RawCryptoOhlcv",
    "CuratedCryptoOhlcv",
    "RawConsultation",
    "RawMajorNews",
    "RawFinancialReports",
    "RawFinancialIndicators",
    "RefStockBasic",
    "RefTradeCal",
    "RefAdjFactor",
    "PipelineLog",
    "RawTopInst",
    "RawLimitList",
    "RawTopList",
]
