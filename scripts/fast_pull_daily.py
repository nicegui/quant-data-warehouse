"""全量A股日线数据拉取（优化版）
- 按月批量拉取 Tushare daily API
- 批量 INSERT (一次 500 行)
- 加速到 0.1s 间隔 (Tushare Pro 允许 200次/分钟)
"""
import os, sys, time, math, json, calendar, logging
from datetime import datetime

import tushare as ts
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ─── Config ───
token = os.environ.get("TUSHARE_TOKEN")
if not token:
    env_path = "/Users/admin/quant-data-warehouse/.env"
    with open(env_path) as f:
        for line in f:
            if line.startswith("TUSHARE_TOKEN="):
                token = line.strip().split("=", 1)[1].strip("'\"")
ts.set_token(token)
pro = ts.pro_api()

engine = create_engine("postgresql://quant:quant_pass@localhost:5432/quantdb",
                       pool_pre_ping=True, pool_size=5, max_overflow=10)

TS_COLS = {'trade_date'}  # Need timestamptz conversion
AUTO_COLS = {'id', 'asset_id', 'created_at', 'updated_at'}

def bulk_upsert(table, df, pk_cols=None):
    """Bulk INSERT with ON CONFLICT DO NOTHING"""
    if df is None or df.empty:
        return 0
    
    df.columns = [c.lower() for c in df.columns]
    
    # Get table columns
    with engine.connect() as conn:
        r = conn.execute(text(f"""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name='{table}'
        """))
        col_types = {row[0]: row[1] for row in r.fetchall()}
    
    existing_cols = set(col_types.keys())
    common_cols = [c for c in df.columns if c in existing_cols and c not in AUTO_COLS]
    if not common_cols:
        return 0
    
    df = df[common_cols]
    
    conflict_clause = ''
    if pk_cols:
        conflict_pk = ', '.join(f'"{p}"' for p in pk_cols)
        conflict_clause = f' ON CONFLICT ({conflict_pk}) DO NOTHING'
    
    cols_str = ', '.join(f'"{c}"' for c in df.columns)
    
    total = 0
    BATCH = 500
    for start in range(0, len(df), BATCH):
        batch = df.iloc[start:start+BATCH]
        
        # Build multi-row VALUES
        all_vals = []
        for _, row in batch.iterrows():
            vals = []
            for c in df.columns:
                v = row[c]
                if v is None or (isinstance(v, float) and (v != v or math.isinf(v))):
                    vals.append('NULL')
                elif c in TS_COLS and isinstance(v, str):
                    s = v.strip()
                    if len(s) == 8 and s.isdigit():
                        s = f'{s[:4]}-{s[4:6]}-{s[6:8]}'
                    vals.append(f"'{s.replace(chr(39), chr(39)+chr(39))}'::timestamptz")
                elif isinstance(v, str):
                    vals.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(v, (int, float, np.integer, np.floating)):
                    if isinstance(v, float) and (math.isinf(float(v)) or math.isnan(float(v))):
                        vals.append('NULL')
                    else:
                        vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append('TRUE' if v else 'FALSE')
                else:
                    vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
            all_vals.append(f'({", ".join(vals)})')
        
        sql = f'INSERT INTO "{table}" ({cols_str}) VALUES\n' + ',\n'.join(all_vals) + conflict_clause
        
        with engine.begin() as conn:
            conn.execute(text(sql))
        
        total += len(batch)
    
    return total

def pull_all_stock_daily():
    start_time = time.time()
    log.info("=== 全量A股日线拉取 ===")
    
    total_inserted = 0
    total_skipped = 0
    
    for y in range(1990, 2027):
        for m in range(1, 13):
            if y == 1990 and m < 12:
                continue  # A股最早数据 1990-12-19
            if y == 2026 and m > datetime.now().month:
                continue
            
            start = f'{y}{m:02d}01'
            last_day = calendar.monthrange(y, m)[1]
            end = f'{y}{m:02d}{last_day:02d}'
            
            try:
                df = pro.daily(start_date=start, end_date=end)
                time.sleep(0.1)
                
                if df is None or df.empty:
                    continue
                
                rows_before = len(df)
                n = bulk_upsert('raw_stock_daily', df, pk_cols=['ts_code', 'trade_date'])
                inserted = n
                skipped = rows_before - inserted
                total_inserted += inserted
                total_skipped += skipped
                
                elapsed = time.time() - start_time
                log.info(f"  {y}-{m:02d}: {rows_before} rows (new={inserted}, dup={skipped}) | total={total_inserted:,} | {elapsed:.0f}s")
                
            except Exception as e:
                if '频率过快' in str(e):
                    log.warning(f"  频率限制，等待5s...")
                    time.sleep(5)
                    continue
                log.warning(f"  {y}-{m:02d}: {e}")
                time.sleep(3)
    
    elapsed = time.time() - start_time
    log.info(f"\n=== 完成! 耗时 {elapsed/60:.1f} 分钟 ===")
    log.info(f"  新增: {total_inserted:,} 行")
    log.info(f"  跳过: {total_skipped:,} 行")
    
    # Final count
    with engine.connect() as conn:
        cur = conn.execute(text("SELECT COUNT(*) FROM raw_stock_daily")).scalar()
    log.info(f"  raw_stock_daily 总量: {cur:,}")

if __name__ == '__main__':
    pull_all_stock_daily()
