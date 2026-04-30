#!/usr/bin/env python3
"""Pull stock_daily data.

Usage:
  python scripts/pull/stock_daily.py              # Latest
  python scripts/pull/stock_daily.py --full        # All history
  python scripts/pull/stock_daily.py --date YYYYMMDD
  python scripts/pull/stock_daily.py --start YYYYMMDD --end YYYYMMDD
"""
import sys
import os
import argparse
import calendar
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config.settings import settings
from src.pipeline.engine import run_pipeline
from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("pull.stock_daily")


def get_collector():
    from src.collectors.impl.stock_daily import StockDailyCollector

    return StockDailyCollector(settings.tushare.token)


def pull_latest():
    """Pull latest trading day."""
    collector = get_collector()
    result = run_pipeline(collector, export=False, compute_curated=False)
    log.info(f"Latest: {result}")
    return result


def pull_history():
    """Pull all historical data month by month."""
    collector = get_collector()
    total = 0

    for y in range(1990, 2027):
        for m in range(1, 13):
            if y == 1990 and m < 12:
                continue
            if y == 2026 and m > datetime.now().month:
                continue
            start = f"{y}{m:02d}01"
            end = f"{y}{m:02d}{calendar.monthrange(y, m)[1]:02d}"

            result = run_pipeline(
                collector,
                export=False,
                compute_curated=False,
                start_date=start,
                end_date=end,
            )
            total += result.get("fetched", 0)
            if result.get("fetched", 0) > 0:
                log.info(f"  {y}-{m:02d}: +{result['fetched']} rows (total: {total:,})")
            time.sleep(0.15)

    log.info(f"Done: {total:,} rows total")


def pull_date(date_str: str):
    """Pull a specific trading date."""
    collector = get_collector()
    result = run_pipeline(collector, export=False, compute_curated=False, trade_date=date_str)
    log.info(f"{date_str}: {result}")


def pull_range(start: str, end: str):
    """Pull a date range."""
    collector = get_collector()
    result = run_pipeline(collector, export=False, compute_curated=False, start_date=start, end_date=end)
    log.info(f"Range {start}-{end}: {result}")


def main():
    parser = argparse.ArgumentParser(description="Pull stock daily data")
    parser.add_argument("--full", action="store_true", help="Full historical pull")
    parser.add_argument("--date", help="Specific trading date (YYYYMMDD)")
    parser.add_argument("--start", help="Start date (YYYYMMDD)")
    parser.add_argument("--end", help="End date (YYYYMMDD)")
    args = parser.parse_args()

    if args.full:
        pull_history()
    elif args.date:
        pull_date(args.date)
    elif args.start or args.end:
        pull_range(args.start or "", args.end or "")
    else:
        pull_latest()


if __name__ == "__main__":
    main()
