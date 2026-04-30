#!/usr/bin/env python3
"""Orchestrate all pull scripts — run specific collectors or all.

Usage:
  python scripts/pull_all.py                          # Run all collectors
  python scripts/pull_all.py stock_daily daily_basic  # Run specific collectors
  python scripts/pull_all.py --list                   # List available collectors
  python scripts/pull_all.py --dry-run                # Show what would run
"""
import sys
import os
import argparse
import subprocess
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("pull_all")


PULL_SCRIPTS = {
    "stock_daily": "scripts/pull/stock_daily.py",
    "stock_basic": "scripts/pull/stock_basic.py",
    "adj_factor": "scripts/pull/adj_factor.py",
    "daily_basic": "scripts/pull/daily_basic.py",
    "consultations": None,  # special handling via run_collector.py
    "financial_reports": None,
    "financial_indicators": None,
    "top_inst": None,
    "moneyflow": None,
    "stk_limit": None,
    "concept": None,
    "index_daily": None,
    "macro": None,
    "futures": None,
    "fund": None,
}


def run_script(script_path: str, args: list[str] | None = None) -> dict:
    """Run a pull script via subprocess and return result info."""
    if args is None:
        args = []

    full_path = os.path.join(os.path.dirname(__file__), "..", script_path)
    if not os.path.exists(full_path):
        log.warning(f"Script not found: {full_path}")
        return {"status": "skipped", "reason": "not_found"}

    cmd = [sys.executable, full_path] + args
    log.info(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), ".."))

    if result.returncode != 0:
        log.error(f"Failed: {script_path}\n{result.stderr}")
        return {"status": "failed", "exit_code": result.returncode, "stderr": result.stderr}

    # Log stdout (the log messages from the script)
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            log.info(f"  {line.strip()}")

    return {"status": "success"}


def run_through_run_collector(name: str) -> dict:
    """Run a collector via the generic run_collector.py."""
    run_collector = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_collector.py")
    if not os.path.exists(run_collector):
        log.warning(f"run_collector.py not found")
        return {"status": "skipped", "reason": "not_found"}

    cmd = [sys.executable, run_collector, name]
    log.info(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), ".."))

    if result.returncode != 0:
        log.error(f"Failed: {name}\n{result.stderr}")
        return {"status": "failed", "exit_code": result.returncode}

    for line in result.stdout.strip().split("\n"):
        if line.strip():
            log.info(f"  {line.strip()}")

    return {"status": "success"}


def run_collector(name: str, args: list[str] | None = None) -> dict:
    """Run a collector by name, using dedicated pull script or fallback."""
    if args is None:
        args = []

    script = PULL_SCRIPTS.get(name)
    if script:
        return run_script(script, args)
    else:
        return run_through_run_collector(name)


def list_collectors():
    """Print available collectors."""
    print("Available collectors:")
    print()

    # With dedicated pull scripts
    has_scripts = [n for n, s in PULL_SCRIPTS.items() if s is not None]
    print(f"Dedicated pull scripts ({len(has_scripts)}):")
    for name in sorted(has_scripts):
        print(f"  - {name}")

    # Via run_collector.py fallback
    fallback = [n for n, s in PULL_SCRIPTS.items() if s is None]
    print(f"\nFallback via run_collector.py ({len(fallback)}):")
    for name in sorted(fallback):
        print(f"  - {name}")


def main():
    parser = argparse.ArgumentParser(description="Orchestrate data pull scripts")
    parser.add_argument("collectors", nargs="*", help="Collectors to run (default: all)")
    parser.add_argument("--list", action="store_true", help="List available collectors")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between collectors (seconds)")
    args = parser.parse_args()

    if args.list:
        list_collectors()
        return

    # Determine which collectors to run
    if args.collectors:
        to_run = [c for c in args.collectors if c in PULL_SCRIPTS]
        unknown = [c for c in args.collectors if c not in PULL_SCRIPTS]
        if unknown:
            log.warning(f"Unknown collectors: {', '.join(unknown)}")
    else:
        to_run = list(PULL_SCRIPTS.keys())

    log.info(f"Running {len(to_run)} collectors: {', '.join(to_run)}")

    if args.dry_run:
        log.info("Dry run — would execute:")
        for name in to_run:
            script = PULL_SCRIPTS.get(name)
            if script:
                log.info(f"  python {script}")
            else:
                log.info(f"  python scripts/run_collector.py {name}")
        return

    results = {}
    for i, name in enumerate(to_run):
        if i > 0:
            time.sleep(args.delay)

        log.info("=" * 60)
        log.info(f"[{i+1}/{len(to_run)}] Running: {name}")
        results[name] = run_collector(name)

    # Summary
    log.info("=" * 60)
    log.info("Summary:")
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    log.info(f"  Success: {success_count}, Failed: {failed_count}, Total: {len(results)}")

    if failed_count > 0:
        for name, result in results.items():
            if result["status"] == "failed":
                log.warning(f"  {name}: FAILED ({result.get('stderr', 'see above')})")
        sys.exit(1)


if __name__ == "__main__":
    main()
