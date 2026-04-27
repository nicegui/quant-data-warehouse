"""Parquet export — PostgreSQL curated layer → Hive-partitioned Parquet files.

Exports curated data as Hive-partitioned Parquet files for DuckDB/Polars analysis.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.config.settings import settings
from src.db.engine import get_engine
from src.utils.logging import get_logger

logger = get_logger("pipeline.parquet")

# Table export config: (schema.table, parquet_dir, partition_cols)
EXPORT_TABLES = [
    {
        "sql": "SELECT * FROM curated_stock_daily_adj",
        "dir": "curated/stock_daily_adj",
        "partition_cols": None,  # Single parquet for now, add partitioning later
    },
    {
        "sql": "SELECT * FROM raw_consultation",
        "dir": "raw/consultation",
        "partition_cols": None,
    },
    {
        "sql": "SELECT * FROM ref_stock_basic",
        "dir": "ref/stock_basic",
        "partition_cols": None,
    },
    {
        "sql": "SELECT * FROM ref_adj_factor",
        "dir": "ref/adj_factor",
        "partition_cols": None,
    },
]


class ParquetExporter:
    """Export PostgreSQL tables to Hive-partitioned Parquet."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.data_dir / "parquet"

    def export_table(self, sql: str, output_dir: Path) -> int:
        """Export a SQL query result to Parquet.

        Returns number of rows written.
        """
        engine = get_engine()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read from PostgreSQL via Polars
        df = pl.read_database(sql, connection=engine)

        if df.is_empty():
            logger.info("Table empty, skipping: %s", sql[:60])
            return 0

        # Write as single Parquet file
        file_path = output_dir / "data.parquet"
        df.write_parquet(str(file_path))

        rows = len(df)
        logger.info("Exported %d rows to %s", rows, file_path)
        return rows

    def export_all(self) -> dict[str, int]:
        """Export all configured tables.

        Returns dict of table_name -> rows_exported.
        """
        results = {}
        for config in EXPORT_TABLES:
            sql = config["sql"]
            output_dir = self.base_dir / config["dir"]
            try:
                rows = self.export_table(sql, output_dir)
                results[config["dir"]] = rows
            except Exception as e:
                logger.error("Export failed for %s: %s", config["dir"], e)
                results[config["dir"]] = -1
        return results
