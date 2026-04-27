#!/usr/bin/env python3
"""Start the periodic data collection scheduler.

Reads YAML source configs and registers all cron jobs,
then starts the scheduler (runs forever).
"""

import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import settings
from src.pipeline.scheduler import DataScheduler
from src.collectors.tushare_collector import (
    StockDailyCollector,
    ConsultationCollector,
    FinancialReportCollector,
    FinancialIndicatorCollector,
    StockBasicCollector,
    AdjFactorCollector,
)
from src.pipeline.engine import run_pipeline
from src.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("run_scheduler")


def make_collector_fn(name, cls, export=False, curated=False, **collector_kwargs):
    def _run():
        token = settings.tushare.token
        collector = cls(token=token)
        return run_pipeline(
            collector,
            export=export,
            compute_curated=curated,
            **collector_kwargs,
        )
    _run.__name__ = name
    return _run


def main():
    scheduler = DataScheduler()

    # Load YAML source configs
    tushare_cfg = settings.load_source_config("tushare")
    sources = tushare_cfg.get("sources", {})

    collector_map = {
        "stock_daily": (StockDailyCollector, True, True),
        "consultations": (ConsultationCollector, False, False),
        "financial_reports": (FinancialReportCollector, False, False),
        "financial_indicators": (FinancialIndicatorCollector, False, False),
        "stock_basic": (StockBasicCollector, True, False),
        "adj_factor": (AdjFactorCollector, True, False),
    }

    for source_name, source_cfg in sources.items():
        schedule = source_cfg.get("schedule")
        if not schedule:
            continue

        cls, default_export, default_curated = collector_map.get(
            source_name, (None, False, False)
        )
        if cls is None:
            continue

        export = source_cfg.get("export", default_export)
        curated = source_cfg.get("curated", default_curated)

        fn = make_collector_fn(
            source_name, cls, export=export, curated=curated,
            **source_cfg.get("params", {}),
        )
        scheduler.add_cron(source_name, fn, schedule)

    logger.info("Registered %d jobs", len(scheduler.get_jobs()))

    def shutdown(signum, frame):
        logger.info("Received signal %s, shutting down...", signum)
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    signal.pause()


if __name__ == "__main__":
    main()
