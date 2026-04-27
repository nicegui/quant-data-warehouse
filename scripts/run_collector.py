#!/usr/bin/env python3
"""Run a specific data collector pipeline.

Usage:
    python scripts/run_collector.py stock_daily [--export] [--curated]
    python scripts/run_collector.py consultations
    python scripts/run_collector.py financial_reports
    python scripts/run_collector.py stock_basic
    python scripts/run_collector.py adj_factor
    python scripts/run_collector.py all
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import settings
from src.collectors.tushare_collector import (
    StockDailyCollector,
    ConsultationCollector,
    FinancialReportCollector,
    FinancialIndicatorCollector,
    StockBasicCollector,
    AdjFactorCollector,
    TopInstCollector,
    DailyBasicCollector,
    MoneyflowCollector,
    StkLimitCollector,
    ConceptCollector,
    IndexCollector,
    MacroCollector,
    FuturesCollector,
    FundCollector,
)
from src.pipeline.engine import run_pipeline
from src.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("run_collector")


COLLECTORS = {
    "stock_daily": {
        "cls": StockDailyCollector,
        "params": {},
        "export": True,
        "curated": True,
    },
    "daily_basic": {
        "cls": DailyBasicCollector,
        "params": {},
        "export": True,
        "curated": False,
    },
    "consultations": {
        "cls": ConsultationCollector,
        "params": {"src": "sina"},
        "export": True,
        "curated": False,
    },
    "financial_reports": {
        "cls": FinancialReportCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "financial_indicators": {
        "cls": FinancialIndicatorCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "stock_basic": {
        "cls": StockBasicCollector,
        "params": {},
        "export": True,
        "curated": False,
    },
    "adj_factor": {
        "cls": AdjFactorCollector,
        "params": {},
        "export": True,
        "curated": False,
    },
    "top_inst": {
        "cls": TopInstCollector,
        "params": {},
        "export": True,
        "curated": False,
    },
    "stk_limit": {
        "cls": StkLimitCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "concept": {
        "cls": ConceptCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "index_daily": {
        "cls": IndexCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "macro": {
        "cls": MacroCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "futures": {
        "cls": FuturesCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
    "fund": {
        "cls": FundCollector,
        "params": {},
        "export": False,
        "curated": False,
    },
}


def run_single(name: str, export: bool = False, curated: bool = False):
    cfg = COLLECTORS.get(name)
    if not cfg:
        logger.error("Unknown collector: %s", name)
        logger.info("Available: %s", ", ".join(COLLECTORS.keys()))
        return

    collector = cfg["cls"](token=settings.tushare.token)
    result = run_pipeline(
        collector,
        export=export or cfg["export"],
        compute_curated=curated or cfg["curated"],
        **cfg["params"],
    )
    logger.info("Result: %s", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Run data collector pipeline")
    parser.add_argument("collector", nargs="?", help="Collector name or 'all'")
    parser.add_argument("--export", action="store_true", help="Export to Parquet")
    parser.add_argument("--curated", action="store_true", help="Compute curated layer")
    args = parser.parse_args()

    if not args.collector:
        parser.print_help()
        return

    if args.collector == "all":
        for name in COLLECTORS:
            logger.info("=" * 60)
            logger.info("Running collector: %s", name)
            run_single(name, export=args.export, curated=args.curated)
    else:
        run_single(args.collector, export=args.export, curated=args.curated)


if __name__ == "__main__":
    main()
