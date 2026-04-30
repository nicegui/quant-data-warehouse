#!/usr/bin/env python3
"""全量数据初始化 — 按优先级拉取所有数据源。

策略:
1. 参考数据先到位（trade_cal, concept, stock_basic done）
2. 行情类大表按月分批（daily_basic，index_daily）
3. 基本面逐个股票 (financial)
4. 资金面（moneyflow, top_inst, margin, hsgt）
5. 新闻快讯（consultations, major_news）
6. 扩展品种（futures, fund, macro）
7. 收尾（parquet export, curated compute）

用法:
  python scripts/full_data_init.py              # 全量
  python scripts/full_data_init.py --dry-run     # 预览
  python scripts/full_data_init.py --batch 1     # 只跑第1批
"""
import sys, os, time, argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("full_data_init")

# ─── Batch definitions ────────────────────────────────────────────────
# Each batch is a list of (collector_name, {params})
# "special" handlers are for non-standard pull patterns

BATCHES = {
    "batch1_refdata": {  # 参考数据 — 快
        "trade_cal": {"start_date": "19900101", "end_date": "20261231"},
        "concept": {},
        "adj_factor_latest": {},  # Will use single daily pull
    },
    "batch2_stock_basic_year": {  # 全A股行情 — 最核心
        "stock_daily_full_year": {"year": 2026},
        "stock_daily_full_year": {"year": 2025},
        "stock_daily_full_year": {"year": 2024},
        "stock_daily_full_year": {"year": 2023},
    },
    "batch3_daily_basic": {  # PE/PB/换手率/市值 — 按月
        "daily_basic": {"start_date": "20240101", "end_date": "20260428"},
    },
    "batch4_financial": {  # 基本面
        "financial": {"start_date": "20200101"},
    },
    "batch5_moneyflow": {  # 资金面
        "moneyflow": {},
        "top_inst": {},
        "stk_limit": {},
        "index_daily": {},
    },
    "batch6_news": {  # 新闻
        "consultations": {"src": "sina", "limit": 2000},
        "major_news": {"start_date": "20250101"},
    },
    "batch7_extension": {  # 扩展
        "futures": {},
        "fund": {},
        "macro": {},
    },
}

BATCH_ORDER = [
    "batch1_refdata",
    "batch2_stock_basic_year",
    "batch3_daily_basic",
    "batch4_financial",
    "batch5_moneyflow",
    "batch6_news",
    "batch7_extension",
]


def run_pipeline_safe(name: str, **params) -> dict:
    """Run a collector pipeline with error handling."""
    from src.pipeline.engine import run_pipeline
    from src.collectors.tushare_collector import (
        TradeCalCollector, ConceptCollector, AdjFactorCollector,
        DailyBasicCollector, MoneyflowCollector, TopInstCollector,
        StkLimitCollector, IndexCollector, MacroCollector,
        FuturesCollector, FundCollector, ConsultationCollector,
        MajorNewsCollector, FinancialReportCollector,
        FinancialIndicatorCollector, StockDailyCollector,
    )

    COLLECTOR_MAP = {
        "trade_cal": TradeCalCollector,
        "concept": ConceptCollector,
        "adj_factor_latest": AdjFactorCollector,
        "stock_daily_full_year": StockDailyCollector,
        "daily_basic": DailyBasicCollector,
        "financial": (FinancialReportCollector, FinancialIndicatorCollector),
        "moneyflow": MoneyflowCollector,
        "top_inst": TopInstCollector,
        "stk_limit": StkLimitCollector,
        "index_daily": IndexCollector,
        "consultations": ConsultationCollector,
        "major_news": MajorNewsCollector,
        "futures": FuturesCollector,
        "fund": FundCollector,
        "macro": MacroCollector,
    }

    cls = COLLECTOR_MAP.get(name)
    if cls is None:
        return {"status": "skipped", "reason": f"unknown collector: {name}"}

    if isinstance(cls, tuple):
        # Multiple collectors
        results = []
        for c in cls:
            collector = c(token=settings.tushare.token)
            result = run_pipeline(collector, export=False, compute_curated=False, **params)
            results.append(result)
        return {"status": "success", "results": results}

    collector = cls(token=settings.tushare.token)
    return run_pipeline(collector, export=False, compute_curated=False, **params)


def pull_stock_daily_year(year: int):
    """Pull full year stock daily data month by month."""
    from src.config.settings import settings
    from src.pipeline.engine import run_pipeline
    from src.collectors.impl.stock_daily import StockDailyCollector

    collector = StockDailyCollector(token=settings.tushare.token)
    total = 0

    for month in range(1, 13):
        start = f"{year}{month:02d}01"
        if month == 12:
            end = f"{year+1}0101"
        else:
            end = f"{year}{month+1:02d}01"

        log.info(f"  Stock daily: {start} -> {end}")
        try:
            result = run_pipeline(collector, export=False, compute_curated=False, start_date=start, end_date=end)
            w = result.get("written", 0)
            total += w
            log.info(f"  -> {w} rows written (total: {total})")
            time.sleep(0.5)  # Rate limit
        except Exception as e:
            log.warning(f"  -> failed: {e}")

    return total


def pull_daily_basic_full():
    """Pull daily_basic data from 2024 onwards month by month."""
    from src.config.settings import settings
    from src.pipeline.engine import run_pipeline
    from src.collectors.impl.daily_basic import DailyBasicCollector

    collector = DailyBasicCollector(token=settings.tushare.token)
    total = 0

    for year in range(2024, 2027):
        for month in range(1, 13):
            start = f"{year}{month:02d}01"
            if year == 2026 and month > 4:
                break
            if month == 12:
                end = f"{year+1}0101"
            else:
                end = f"{year}{month+1:02d}01"

            log.info(f"  Daily basic: {start} -> {end}")
            try:
                result = run_pipeline(collector, export=False, compute_curated=False, start_date=start, end_date=end)
                w = result.get("written", 0)
                total += w
                log.info(f"  -> {w} rows (total: {total})")
                time.sleep(0.3)
            except Exception as e:
                log.warning(f"  -> failed: {e}")

    return total


def pull_financial_for_all_stocks():
    """Pull financial data for each stock (one-time backfill)."""
    from src.config.settings import settings
    from src.pipeline.engine import run_pipeline
    from src.collectors.impl.financial_indicators import FinancialIndicatorCollector
    from src.collectors.impl.financial_reports import FinancialReportCollector
    from src.db.session import db_session
    from src.models.reference import RefStockBasic

    indicators_collector = FinancialIndicatorCollector(token=settings.tushare.token)
    reports_collector = FinancialReportCollector(token=settings.tushare.token)

    # Get all stock codes
    with db_session() as session:
        stocks = session.query(RefStockBasic.ts_code).all()
    ts_codes = [s[0] for s in stocks]

    total_fin = 0
    total_reports = 0
    log.info(f"Pulling financial data for {len(ts_codes)} stocks...")

    for i, ts_code in enumerate(ts_codes):
        if (i + 1) % 500 == 0:
            log.info(f"  Progress: {i+1}/{len(ts_codes)}")

        try:
            # Financial indicators (ROE, EPS, etc.)
            result = run_pipeline(
                indicators_collector, export=False,
                ts_code=ts_code, start_date="20200101"
            )
            total_fin += result.get("written", 0)

            # Financial reports (main business breakdown)
            result2 = run_pipeline(
                reports_collector, export=False,
                ts_code=ts_code, start_date="20200101"
            )
            total_reports += result2.get("written", 0)
        except Exception as e:
            log.warning(f"  [{i}] {ts_code}: {e}")

        # Rate limit - 200 calls/min max for 5000+ points users
        if (i + 1) % 100 == 0:
            time.sleep(2)
        else:
            time.sleep(0.05)

    return {"total_fin": total_fin, "total_reports": total_reports}


def run_batch(name: str, dry_run: bool = False):
    """Execute a specific batch."""
    tasks = BATCHES.get(name, {})
    log.info(f"\n{'='*60}")
    log.info(f"Batch: {name} ({len(tasks)} collectors)")
    log.info(f"{'='*60}")

    results = {}
    for task_name, params in tasks.items():
        if dry_run:
            log.info(f"  [DRY] Would run: {task_name} {params}")
            results[task_name] = "dry_run"
            continue

        log.info(f"\n--- {task_name} ---")
        start = time.time()

        if task_name == "stock_daily_full_year":
            year = params.get("year", 2026)
            if dry_run:
                log.info(f"  [DRY] Would pull stock_daily for {year}")
            else:
                total = pull_stock_daily_year(year)
                log.info(f"  Completed: {total} rows")
            continue

        if task_name == "daily_basic":
            if dry_run:
                log.info(f"  [DRY] Would pull daily_basic")
            else:
                total = pull_daily_basic_full()
                log.info(f"  Completed: {total} rows")
            continue

        if task_name == "financial":
            if dry_run:
                log.info(f"  [DRY] Would pull financial data for all stocks")
            else:
                res = pull_financial_for_all_stocks()
                log.info(f"  Completed: {res}")
            continue

        if dry_run:
            log.info(f"  [DRY] Would run: {task_name} {params}")
            results[task_name] = "dry_run"
            continue

        result = run_pipeline_safe(task_name, **params)
        elapsed = time.time() - start
        log.info(f"  {task_name}: {result.get('status', '?')} ({elapsed:.0f}s)")
        results[task_name] = result

        # Rate limiting between tasks
        time.sleep(1)

    return results


def check_missing_data():
    """Check what tables have no data that needs initial fill."""
    from src.db.engine import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT relname, n_live_tup
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
        """)).fetchall()

    print(f"\n{'Table':<30} {'Rows':<10} Status")
    print("-" * 50)
    for r in rows:
        status = "✅" if r[1] > 0 else "⬜"
        print(f"{r[0]:<30} {r[1]:<10} {status}")
    print()

    empty = [r[0] for r in rows if r[1] == 0]
    return empty


def main():
    parser = argparse.ArgumentParser(description="Full data initialization")
    parser.add_argument("--batch", choices=BATCH_ORDER + ["all"], default="all",
                        help="Specific batch to run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    parser.add_argument("--check", action="store_true", help="Only check data status")
    args = parser.parse_args()

    if args.check:
        check_missing_data()
        return

    if args.dry_run:
        log.info("DRY RUN MODE - no data will be changed\n")

    # Check current state
    empty_tables = check_missing_data()
    log.info(f"Empty tables: {len(empty_tables)}")

    if args.batch == "all":
        for batch in BATCH_ORDER:
            run_batch(batch, dry_run=args.dry_run)
            time.sleep(2)
    else:
        run_batch(args.batch, dry_run=args.dry_run)

    # Final check
    log.info("\n" + "=" * 60)
    log.info("FINAL STATE:")
    check_missing_data()


if __name__ == "__main__":
    main()
