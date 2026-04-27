"""SQLAlchemy ORM models.

Organization:
  - asset.py      : Unified asset registry (stock, crypto, index, ...)
  - raw/          : Append-only raw data (from API, never mutated)
  - curated/      : Cleaned, adjusted, validated data (SCD2)
  - reference.py  : Reference data (stock_basic, trade_cal, adj_factor)
  - pipeline.py   : Pipeline audit logs
"""

from src.models.base import Base

# Order matters for Alembic autogenerate
from src.models.asset import Asset
from src.models.market import (
    RawStockDaily,
    RawCryptoOhlcv,
    CuratedStockDailyAdj,
    CuratedCryptoOhlcv,
)
from src.models.fundamental import (
    RawFinancialReports,
    CuratedFinancialReports,
)
from src.models.news import (
    RawConsultation,
    RawMajorNews,
)
from src.models.reference import (
    RefStockBasic,
    RefTradeCal,
    RefAdjFactor,
)
from src.models.pipeline import PipelineLog

__all__ = [
    "Base",
    "Asset",
    "RawStockDaily",
    "RawCryptoOhlcv",
    "CuratedStockDailyAdj",
    "CuratedCryptoOhlcv",
    "RawFinancialReports",
    "CuratedFinancialReports",
    "RawConsultation",
    "RawMajorNews",
    "RefStockBasic",
    "RefTradeCal",
    "RefAdjFactor",
    "PipelineLog",
]
