"""stk_factor_pro 并行回填 — 利用 500/min 速率上限。

Fetch: 8 线程并发调用 API
Insert: 单线程 psycopg2 execute_values 高速写入
"""
import os, sys, time, json, queue, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import tushare as ts

load_dotenv(dotenv_path=os.path.expanduser("~/.openclaw/workspace/quant-data-warehouse/.env"))

TOKEN = os.getenv("TUSHARE_TOKEN")
pro = ts.pro_api(TOKEN)

# ── Config ──
WORKERS = 8
INSERT_BATCH = 100
DB_URL = "postgresql:///quantdb"

# ── Get dates (2018+) ──
print("Loading trade calendar...", flush=True)
cal = pro.trade_cal(exchange="SSE", start_date="20180101", end_date="20260501", is_open="1")
dates = sorted(cal["cal_date"].tolist())
print(f"  {len(dates)} trading days ({dates[0]} ~ {dates[-1]})", flush=True)

# ── Get existing pairs to skip ──
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("SELECT ts_code, trade_date FROM raw_stk_factor_pro")
existing = set(cur.fetchall())
cur.close()
conn.close()
print(f"  {len(existing):,} existing rows in DB", flush=True)

# Strip dates we already fully have
date_stock_counts = {}
for ts_code, trade_date in existing:
    d = str(trade_date)
    date_stock_counts[d] = date_stock_counts.get(d, 0) + 1

# A date is "done" if it has >= 5000 rows (typical daily count)
done_dates = {d for d, c in date_stock_counts.items() if c >= 5000}
pending_dates = [d for d in dates if d not in done_dates]
print(f"  {len(done_dates)} dates done, {len(pending_dates)} pending", flush=True)

if not pending_dates:
    print("All dates complete!", flush=True)
    sys.exit(0)

# ── Fetch worker ──
result_queue: queue.Queue = queue.Queue(maxsize=200)
fetch_lock = threading.Lock()
fetch_count = 0
fetch_errors = 0

def fetch_date(trade_date: str):
    """Fetch one date's data and push to queue."""
    global fetch_count, fetch_errors
    try:
        df = pro.stk_factor_pro(trade_date=trade_date)
        with fetch_lock:
            fetch_count += 1
        if df is not None and not df.empty:
            rows = df.to_dict(orient="records")
            # Filter out already-existing rows
            new_rows = [(trade_date, r) for r in rows if (r["ts_code"], trade_date) not in existing]
            if new_rows:
                result_queue.put((trade_date, [r for _, r in new_rows]))
        return len(df) if df is not None else 0
    except Exception as e:
        with fetch_lock:
            fetch_errors += 1
        if fetch_errors <= 5:
            print(f"  FETCH ERROR [{trade_date}]: {e}", flush=True)
        return 0

# ── Insert worker (single thread, psycopg2) ──
COLUMNS = None

def get_columns(rows):
    """Extract column list from first batch."""
    return [k for k in rows[0].keys()]

def insert_batch(conn, rows, columns):
    """Fast insert using execute_values."""
    if not rows:
        return 0
    sql = f"""
        INSERT INTO raw_stk_factor_pro ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (ts_code, trade_date) DO NOTHING
    """
    template = f"({', '.join(['%s'] * len(columns))})"
    values = []
    for r in rows:
        vals = []
        for c in columns:
            v = r.get(c)
            vals.append(v)
        values.append(tuple(vals))
    psycopg2.extras.execute_values(cur, sql, values, template=template)
    conn.commit()
    return len(rows)

# ── Main ──
print(f"\nStarting {WORKERS} fetchers...", flush=True)
t0 = time.time()

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
inserted = 0
flushed = 0

with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = {pool.submit(fetch_date, d): d for d in pending_dates}
    
    done_count = 0
    buffer = []
    
    for future in as_completed(futures):
        trade_date = futures[future]
        done_count += 1
        
        # Collect buffered results
        while not result_queue.empty():
            try:
                _, rows = result_queue.get_nowait()
                buffer.extend(rows)
                result_queue.task_done()
            except queue.Empty:
                break
        
        # Flush when buffer is large enough
        if len(buffer) >= INSERT_BATCH:
            if COLUMNS is None:
                COLUMNS = get_columns(buffer)
            n = insert_batch(conn, buffer[:INSERT_BATCH], COLUMNS)
            inserted += n
            buffer = buffer[INSERT_BATCH:]
            flushed += 1
        
        # Progress
        if done_count % 100 == 0 or done_count <= 5:
            elapsed = time.time() - t0
            rate = done_count / elapsed if elapsed > 0 else 0
            eta = (len(pending_dates) - done_count) / rate if rate > 0 else 0
            with fetch_lock:
                fc = fetch_count
                fe = fetch_errors
            print(f"  [{trade_date}] d={done_count}/{len(pending_dates)} "
                  f"fetched={fc} ins={inserted:,} rate={rate:.1f}d/s ETA={eta:.0f}s err={fe}", flush=True)

    # Final flush
    if buffer:
        if COLUMNS is None:
            COLUMNS = get_columns(buffer)
        n = insert_batch(conn, buffer, COLUMNS)
        inserted += n

cur.close()
conn.close()

elapsed = time.time() - t0
print(f"\nDONE: {len(pending_dates)} dates, {inserted:,} inserted, {elapsed:.0f}s", flush=True)
