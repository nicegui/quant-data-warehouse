#!/usr/bin/env python3
"""Pull adj_factor data.

Usage:
  python scripts/pull/adj_factor.py               # Latest (from 2000-01-01)
  python scripts/pull/adj_factor.py --full         # Same as default
  python scripts/pull/adj_factor.py --date YYYYMMDD
  python scripts/pull/adj_factor.py --start YYYYMMDD --end YYYYMMDD
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config.settings import settings
from src.pipeline.engine import run_pipeline
from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("pull.adj_factor")


def get_collector():
    from src.collectors.impl.adj_factor import AdjFactorCollector

    return AdjFactorCollector(settings.tushare.token)


def pull_latest():
    """Pull all adj factors from 2000-01-01."""
    collector = get_collector()
    result = run_pipeline(collector, export=False, compute_curated=False, start_date="20000101")
    log.info(f"Adj factor: {result}")
    return result


def pull_date(date_str: str):
    """Pull adj factors for a specific date."""
    collector = get_collector()
    result = run_pipeline(collector, export=False, compute_curated=False, trade_date=date_str)
    log.info(f"{date_str}: {result}")


def pull_range(start: str, end: str):
    """Pull adj factors for a date range."""
    collector = get_collector()
    result = run_pipeline(
        collector, export=False, compute_curated=False, start_date=start, end_date=end
    )
    log.info(f"Range {start}-{end}: {result}")


def main():
    parser = argparse.ArgumentParser(description="Pull adj factor data")
    parser.add_argument("--full", action="store_true", help="Full pull from 2000")
    parser.add_argument("--date", help="Specific trading date (YYYYMMDD)")
    parser.add_argument("--start", help="Start date (YYYYMMDD)")
    parser.add_argument("--end", help="End date (YYYYMMDD)")
    args = parser.parse_args()

    if args.date:
        pull_date(args.date)
    elif args.start or args.end:
        pull_range(args.start or "", args.end or "")
    else:
        pull_latest()


if __name__ == "__main__":
    main()
