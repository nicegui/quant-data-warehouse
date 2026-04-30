#!/usr/bin/env python3
"""全量 A 股日线拉取 — 快速版
- 按月批量，0.15s 间隔
- 直接 SQL bulk INSERT (500 行/批)
- 内置断点续传
"""
import os, sys, time, json, calendar, logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config.settings import settings

from sqlalchemy import create_engine, text
import tushare as ts

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

pro = ts.pro_api(settings.tushare.token)
engine = create_engine(settings.db.dsn, pool_pre_ping=True, pool_size=3)

CHECKPOINT = os.path.join(os.path.dirname(__file__), '..', 'data', 'pull_checkpoint.json')
TARGET_COLS = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close',
               'pre_close', 'change', 'pct_chg', 'vol', 'amount']

def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}

def save_checkpoint(data):
    os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
    with open(CHECKPOINT, 'w') as f:
        json.dump(data, f)

def bulk_insert(df):
    """Bulk INSERT with ON CONFLICT DO NOTHING"""
    if df is None or df.empty:
        return 0
    
    df.columns = [c.lower() for c in df.columns]
    common = [c for c in TARGET_COLS if c in df.columns]
    if not common:
        return 0
    
    cols_str = ', '.join(f'"{c}"' for c in common)
    
    BATCH = 500
    total = 0
    for start in range(0, len(df), BATCH):
        batch = df.iloc[start:start+BATCH]
        values = []
        for _, r in batch.iterrows():
            parts = []
            for c in common:
                v = r[c]
                if v is None or (isinstance(v, float) and (v != v or v == float('inf'))):
                    parts.append('NULL')
                elif c == 'trade_date':
                    parts.append(f"'{v}'::date")
                elif isinstance(v, str):
                    escaped = v.replace("'", "''")
                    parts.append(f"'{escaped}'")
                else:
                    parts.append(str(v))
            values.append(f'({",".join(parts)})')
        
        sql = f"INSERT INTO raw_stock_daily ({cols_str}) VALUES\n"
        sql += ',\n'.join(values)
        sql += " ON CONFLICT (ts_code, trade_date) DO NOTHING"
        
        with engine.begin() as conn:
            r = conn.execute(text(sql))
        total += r.rowcount
    
    return total

def main():
    cp = load_checkpoint()
    last_pulled = cp.get('last_month', '199012')
    total_done = cp.get('total', 0)
    log.info(f"=== 全量 A 股日线拉取 (续传从 {last_pulled} 起, 已有 {total_done:,} 行) ===")
    
    start_time = time.time()
    total_inserted = total_done
    total_errors = 0
    
    for y in range(int(last_pulled[:4]), 2027):
        start_m = int(last_pulled[4:6]) if y == int(last_pulled[:4]) else 1
        for m in range(start_m, 13):
            if y == 1990 and m < 12:
                continue
            if y == 2026 and m > datetime.now().month:
                break

            start = f'{y}{m:02d}01'
            last_day = calendar.monthrange(y, m)[1]
            end = f'{y}{m:02d}{last_day:02d}'
            
            try:
                t0 = time.time()
                df = pro.daily(start_date=start, end_date=end)
                api_time = time.time() - t0
                time.sleep(max(0.12, 0.3 - api_time))
                
                if df is None or df.empty:
                    elapsed = time.time() - start_time
                    log.info(f"  [{y}-{m:02d}] 无数据 | {elapsed:.0f}s")
                    save_checkpoint({'last_month': f'{y}{m:02d}', 'total': total_inserted})
                    continue
                
                n = bulk_insert(df)
                total_inserted += n
                elapsed = time.time() - start_time
                log.info(f"  [{y}-{m:02d}] +{n} rows (total: {total_inserted:,}) | {elapsed:.0f}s")
                save_checkpoint({'last_month': f'{y}{m:02d}', 'total': total_inserted})
                
            except Exception as e:
                total_errors += 1
                log.warning(f"  [{y}-{m:02d}] ERROR: {e}")
                time.sleep(3)
    
    elapsed = time.time() - start_time
    log.info(f"\n=== 完成! {elapsed/60:.1f} 分钟 ===")
    log.info(f"  新增: {total_inserted - total_done:,} 行")
    log.info(f"  总量: {total_inserted:,}")
    log.info(f"  错误: {total_errors}")
    
    with engine.connect() as c:
        cur = c.execute(text("SELECT COUNT(*) FROM raw_stock_daily"))
        log.info(f"  raw_stock_daily 校验: {cur.scalar():,}")
    
    if os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)

if __name__ == '__main__':
    main()
