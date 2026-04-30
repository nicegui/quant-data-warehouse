"""全量 A 股日线拉取（适配本地环境）
按月批量，0.1s 间隔，批处理写入
"""
import os, sys, time, calendar, logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.settings import settings
from src.collectors.tushare_collector import StockDailyCollector
from src.pipeline.engine import run_pipeline
from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("pull_history")

def main():
    collector = StockDailyCollector(settings.tushare.token)
    start_time = time.time()
    total_inserted = 0
    total_skipped = 0
    month_count = 0

    log.info("=== 全量 A 股日线拉取开始 ===")

    for y in range(1990, 2027):
        for m in range(1, 13):
            if y == 1990 and m < 12:
                continue  # A股最早 1990-12
            if y == 2026 and m > datetime.now().month:
                continue

            start = f'{y}{m:02d}01'
            last_day = calendar.monthrange(y, m)[1]
            end = f'{y}{m:02d}{last_day:02d}'

            # Use start_date/end_date by month
            try:
                result = run_pipeline(
                    collector, export=False, compute_curated=False,
                    start_date=start, end_date=end
                )
            except Exception as e:
                log.warning(f"  {y}-{m:02d}: {e}")
                time.sleep(3)
                continue

            fetched = result.get("fetched", 0)
            written = result.get("written", 0)

            elapsed = time.time() - start_time
            if fetched > 0:
                total_inserted += fetched
                month_count += 1
                log.info(f"  {y}-{m:02d}: {fetched} rows | total={total_inserted:,} | {elapsed:.0f}s")

            # Tushare rate: 200 req/min → 0.3s between calls
            time.sleep(0.15)

    elapsed = time.time() - start_time
    log.info(f"\n=== 完成! 耗时 {elapsed/60:.1f} 分钟 ===")
    log.info(f"  月份数: {month_count}")
    log.info(f"  总行数: {total_inserted:,}")

    # Count final
    from src.db.engine import get_engine
    from sqlalchemy import text
    engine = get_engine()
    with engine.connect() as c:
        cur = c.execute(text("SELECT COUNT(*) FROM raw_stock_daily"))
        log.info(f"  raw_stock_daily 总量: {cur.scalar():,}")

if __name__ == '__main__':
    main()
