#!/usr/bin/env python3
"""Compute the Fear & Greed Index for A-shares.

Usage:
    python scripts/compute_fgi.py              # latest reading
    python scripts/compute_fgi.py --full       # full history to CSV
    python scripts/compute_fgi.py --json       # latest as JSON
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    stream=sys.stdout,
)

from src.research.fgi.engine import compute_fgi, latest_fgi


def main():
    parser = argparse.ArgumentParser(description="A-share Fear & Greed Index")
    parser.add_argument("--full", action="store_true", help="Compute full history")
    parser.add_argument("--json", action="store_true", help="Latest as JSON")
    parser.add_argument("--csv", type=str, help="Save full history to CSV file")
    parser.add_argument("--tail", type=int, default=10, help="Show last N rows (--full mode)")
    args = parser.parse_args()

    if args.json:
        import json
        print(json.dumps(latest_fgi(), ensure_ascii=False, indent=2))
        return

    if args.full or args.csv:
        df = compute_fgi()
        cols = ["date", "fgi", "sentiment", "indicators_available"] + [
            "price_momentum", "market_breadth", "volatility",
            "volume", "margin_sentiment", "limit_ratio",
            "northbound", "turnover",
        ]
        available = [c for c in cols if c in df.columns]

        if args.csv:
            df[available].to_csv(args.csv, index=False)
            print(f"Saved {len(df)} rows to {args.csv}")
        else:
            print(df[available].tail(args.tail).to_string(index=False))
        return

    # Default: latest reading
    result = latest_fgi()
    print(f"\n{'='*50}")
    print(f"  A股恐惧贪婪指数")
    print(f"{'='*50}")
    print(f"  📅 {result['date']}")
    print(f"  📊 FGI: {result['fgi']}  ({result['sentiment']})")
    print(f"  📋 有效指标: {result['indicators_available']}/8")
    print(f"{'='*50}")
    print(f"\n  子指标分数:")
    for name, score in result.get("sub_scores", {}).items():
        bar = "█" * int(score / 5) if score else "—"
        print(f"  {name:20s} {score:5.1f}  {bar}")


if __name__ == "__main__":
    main()
