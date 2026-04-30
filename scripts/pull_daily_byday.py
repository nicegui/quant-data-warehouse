#!/usr/bin/env python3
"""A 股日线按天拉取 — 并行版
- 按交易日逐天拉取 (每天~5500行)
- 8线程 + 令牌桶限流 (170 req/min)
- 内置断点续传，容错NULL值
"""
import os, sys, time, json, logging, threading
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config.settings import settings

from sqlalchemy import create_engine, text
import tushare as ts

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

TOKEN = settings.tushare.token
DB_URL = settings.db.dsn
THREADS = 8
RATE_LIMIT = 170  # requests/min (max is 200)

CHECKPOINT = os.path.join(os.path.dirname(__file__), '..', 'data', 'pull_checkpoint.json')

# ─── Token bucket rate limiter ───
class TokenBucket:
    def __init__(self, rate_per_min, burst=5):
        self.max_tokens = rate_per_min
        self.rate = rate_per_min / 60.0
        self.tokens = burst
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self):
        deadline = time.time() + 600
        while time.time() < deadline:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
                self.last_refill = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            time.sleep(min(wait, 0.5))

bucket = TokenBucket(RATE_LIMIT)


def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {'done_dates': []}


def save_checkpoint(data):
    os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
    with open(CHECKPOINT, 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def safe(v, default=0):
    """Handle None/NaN/inf"""
    if v is None:
        return default
    if isinstance(v, float):
        if v != v or v == float('inf') or v == float('-inf'):
            return default
    return v


def pull_day(engine, trade_date):
    """Pull data for a single trading day and insert into DB"""
    pro = ts.pro_api(TOKEN)
    df = pro.daily(trade_date=trade_date)

    if df is None or df.empty:
        return 0

    df.columns = [c.lower() for c in df.columns]
    target_cols = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close',
                   'pre_close', 'change', 'pct_chg', 'vol', 'amount']
    common = [c for c in target_cols if c in df.columns]
    if not common:
        return 0

    cols_str = ', '.join(f'"{c}"' for c in common)
    total = 0

    # Build all values first
    all_values = []
    for _, r in df.iterrows():
        parts = []
        for c in common:
            v = r.get(c)
            if c == 'trade_date':
                parts.append(f"'{v}'::date")
            elif c == 'ts_code':
                parts.append(f"'{safe(v, '')}'")
            elif isinstance(v, str):
                parts.append(f"'{v.replace(chr(39), chr(39)*2)}'")
            else:
                cleaned = safe(v, 0)
                parts.append(str(cleaned))
        all_values.append(f'({",".join(parts)})')

    BATCH = 1000
    for i in range(0, len(all_values), BATCH):
        chunk = all_values[i:i+BATCH]
        sql = f"INSERT INTO raw_stock_daily ({cols_str}) VALUES\n"
        sql += ',\n'.join(chunk)
        sql += " ON CONFLICT (ts_code, trade_date) DO NOTHING"
        with engine.begin() as conn:
            r = conn.execute(text(sql))
        total += r.rowcount

    return total


def get_trading_days(engine):
    """Get all trading days from Tushare"""
    cp = load_checkpoint()
    if 'trading_days' in cp:
        return cp['trading_days']

    pro = ts.pro_api(TOKEN)
    df = pro.trade_cal(start_date='19901201', end_date='20261231')
    trading_days = sorted(d.replace('-', '') for d in df[df['is_open'] == 1]['cal_date'].tolist())
    log.info(f"Total trading days: {len(trading_days)} ({trading_days[0]} ~ {trading_days[-1]})")
    cp['trading_days'] = trading_days
    save_checkpoint(cp)
    return trading_days


def get_done_dates(engine):
    """Get dates already in DB"""
    cp = load_checkpoint()
    done = set(cp.get('done_dates', []))
    try:
        with engine.connect() as c:
            r = c.execute(text("SELECT DISTINCT to_char(trade_date, 'YYYYMMDD') FROM raw_stock_daily"))
            done |= set(r.scalars().all())
    except:
        pass
    return done


def worker(dates, results, idx, engine):
    """Worker thread"""
    count = 0
    errors = 0
    for date in dates:
        bucket.acquire()
        try:
            n = pull_day(engine, date)
            if n > 0:
                count += n
            if n == 0:
                log.debug(f"  [T{idx}] {date}: 0 rows")
            elif n % 1000 == 0:
                log.info(f"  [T{idx}] {date}: +{n} (total: {count:,})")
        except Exception as e:
            errors += 1
            err_str = str(e)[:80]
            log.warning(f"  [T{idx}] {date}: {err_str}")
            # save checkpoint on error so we don't redo
            cp = load_checkpoint()
            if date not in cp.get('done_dates', []):
                cp.setdefault('done_dates', []).append(date)
                save_checkpoint(cp)
            time.sleep(1)

    results[idx] = {'count': count, 'errors': errors}
    log.info(f"  🏁 Thread {idx}: {count:,} rows, {errors} errors")


def main():
    engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=2)

    # Get trading days and done dates
    all_days = get_trading_days(engine)
    done = get_done_dates(engine)
    log.info(f"Already done: {len(done)} days")

    # Filter pending
    pending = sorted(set(all_days) - done)
    log.info(f"Pending: {len(pending)} days")

    if not pending:
        log.info("✅ All done!")
        return

    # Split into chunks for threads
    chunk_size = (len(pending) + THREADS - 1) // THREADS
    chunks = [pending[i:i+chunk_size] for i in range(0, len(pending), chunk_size)]

    start_time = time.time()
    results = {}
    threads = []

    for idx, chunk in enumerate(chunks[:THREADS]):
        eng = create_engine(DB_URL, pool_pre_ping=True, pool_size=2)
        t = threading.Thread(target=worker, args=(chunk, results, idx, eng))
        threads.append(t)
        t.start()
        log.info(f"  Started thread {idx}: {len(chunk)} days")

    for t in threads:
        t.join()

    total_rows = sum(r['count'] for r in results.values() if r)
    total_errors = sum(r['errors'] for r in results.values() if r)
    elapsed = time.time() - start_time

    log.info(f"\n=== Done! {elapsed/60:.1f} min ===")
    log.info(f"  Total rows: {total_rows:,}")
    log.info(f"  Errors: {total_errors}")

    # Final count
    with engine.connect() as c:
        cnt = c.execute(text("SELECT COUNT(*) FROM raw_stock_daily")).scalar()
        dates = c.execute(text("SELECT COUNT(DISTINCT trade_date) FROM raw_stock_daily")).scalar()
        log.info(f"  raw_stock_daily: {cnt:,} rows, {dates} days")


if __name__ == '__main__':
    main()
