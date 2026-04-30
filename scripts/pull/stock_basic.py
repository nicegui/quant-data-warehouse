#!/usr/bin/env python3
"""Pull stock_basic data.

Usage:
  python scripts/pull/stock_basic.py              # Latest (full refresh)
  python scripts/pull/stock_basic.py --full        # Same as default (full refresh)
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config.settings import settings
from src.pipeline.engine import run_pipeline
from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("pull.stock_basic")


def get_collector():
    from src.collectors.impl.stock_basic import StockBasicCollector

    return StockBasicCollector(settings.tushare.token)


def pull_full():
    """Full refresh of stock basic data."""
    collector = get_collector()
    result = run_pipeline(collector, export=False, compute_curated=False)
    log.info(f"Stock basic refresh: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Pull stock basic data")
    parser.add_argument("--full", action="store_true", help="Full refresh (default)")
    args = parser.parse_args()

    pull_full()


if __name__ == "__main__":
    main()
