"""全量A股日线 - 按天拉取并行版
- 按天：每天 ~5500 行，一次 API 调用刚刚好
- 并行：10 线程 + 共享令牌桶限流（200 req/min）
- 批量：每 500 行一个 INSERT
"""
import os, sys, time, math, logging
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore
import threading

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

THREADS = 10
REQS_PER_MIN = 180  # Leave margin under 200
MIN_INTERVAL = 60.0 / REQS_PER_MIN  # ~0.33s between API calls

TS_COLS = {'trade_date'}
AUTO_COLS = {'id', 'asset_id', 'created_at', 'updated_at'}

# ─── Rate limiter (token bucket, thread-safe) ───
class RateLimiter:
    def __init__(self, rate_per_sec, burst=5):
        self.rate = rate_per_sec
        self.burst = burst
        self.tokens = burst
        self.last_refill = time.time()
        self.lock = Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return  # Got token immediately
            else:
                wait = (1 - self.tokens) / self.rate
                self.tokens = 0
                # Another thread will refill
        time.sleep(wait)
        with self.lock:
            self.tokens -= 1

rate_limiter = RateLimiter(REQS_PER_MIN / 60.0, burst=5)

# ─── DB ───
def get_engine():
    return create_engine("postgresql://quant:quant_pass@localhost:5432/quantdb",
                         pool_pre_ping=True, pool_size=2)

def bulk_upsert(engine, table, df, pk_cols=None):
    if df is None or df.empty:
        return 0
    
    df.columns = [c.lower() for c in df.columns]
    
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

# ─── Get all trading days ───
engine = get_engine()
trade_dates = pd.read_sql(
    text("SELECT cal_date::date FROM ref_trade_cal WHERE exchange='SSE' AND is_open=true AND cal_date >= '1990-12-19' AND cal_date <= CURRENT_DATE ORDER BY cal_date"),
    engine
)
engine.dispose()

all_dates = [d.strftime('%Y%m%d') for d in trade_dates['cal_date']]
log.info(f"总交易日数: {len(all_dates)}")

# ─── Progress tracker ───
lock = Lock()
total_inserted = 0
total_done = 0
start_time = time.time()

def process_date(trade_date_str):
    global total_inserted, total_done
    
    rate_limiter.acquire()  # Throttle API calls
    
    engine = get_engine()
    
    try:
        pro = ts.pro_api()
        df = pro.daily(trade_date=trade_date_str)
        
        if df is not None and not df.empty:
            n = bulk_upsert(engine, 'raw_stock_daily', df, pk_cols=['ts_code', 'trade_date'])
        else:
            n = 0
        
        with lock:
            total_inserted += n
            total_done += 1
            if total_done % 200 == 0:
                elapsed = time.time() - start_time
                rate = total_inserted / elapsed if elapsed > 0 else 0
                log.info(f"  进度: {total_done}/{len(all_dates)} 天 | {total_inserted:,} 行 | {rate:.0f} 行/秒 | {elapsed/60:.1f}分")
        
        return n
    except Exception as e:
        with lock:
            total_done += 1
        if '频率过快' in str(e):
            log.warning(f"  频率限制! {trade_date_str}")
            time.sleep(5)
        else:
            log.warning(f"  {trade_date_str}: {e}")
        return 0
    finally:
        engine.dispose()

# ─── Run ───
log.info(f"开始并行拉取 ({THREADS}线程, {REQS_PER_MIN} req/min)...")

with ThreadPoolExecutor(max_workers=THREADS) as executor:
    futures = [executor.submit(process_date, d) for d in all_dates]
    for future in as_completed(futures):
        pass

elapsed = time.time() - start_time
log.info(f"\n=== 完成! 耗时 {elapsed/60:.1f} 分钟 ===")

engine = get_engine()
cur = pd.read_sql(text("SELECT COUNT(*) as cnt FROM raw_stock_daily"), engine).iloc[0]['cnt']
engine.dispose()
log.info(f"raw_stock_daily 总量: {cur:,}")
