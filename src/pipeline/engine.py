"""Pipeline engine — orchestrates fetch → validate → store → export."""

from __future__ import annotations

from typing import Any

from src.collectors.base import BaseCollector
from src.pipeline.parquet_exporter import ParquetExporter
from src.utils.logging import get_logger

logger = get_logger("pipeline.engine")


def run_pipeline(
    collector: BaseCollector,
    export: bool = False,
    compute_curated: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """Run a full pipeline: collect → (curate) → (export parquet).

    Args:
        collector: A BaseCollector instance.
        export: Whether to export raw/curated data to Parquet.
        compute_curated: Whether to compute curated layer after raw store.

    Returns:
        Dict with status, fetched, written, curated, export info.
    """
    logger.info("Starting pipeline: %s", collector.name)

    # Step 1: Collect raw data
    result = collector.run(**kwargs)

    if result["status"] == "failed":
        logger.error("Pipeline %s failed: %s", collector.name, result.get("error"))
        return result

    logger.info(
        "Pipeline %s: fetched=%d, written=%d",
        collector.name,
        result["fetched"],
        result["written"],
    )

    # Step 2: Compute curated layer (if applicable)
    curated_written = 0
    if compute_curated:
        curated_written = collector.compute_curated()
        logger.info("Curated: %d records written", curated_written)

    # Step 3: Export to Parquet (if requested)
    export_info = {}
    if export:
        exporter = ParquetExporter()
        export_info = exporter.export_all()

    return {
        **result,
        "curated_written": curated_written,
        "export": export_info,
    }
