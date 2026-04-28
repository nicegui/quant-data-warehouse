"""Tushare 全量数据拉取 — 并行版本
═══════════════════════════════════════════
设计:
  - 共享令牌桶限流器 (180 token/min ⇒ 3 token/sec)
  - 每个 API 调用前 acquire(1 token)
  - 不同类型的表用独立线程拉取，共享同一个限流器
  - 避免超出 Tushare 限流被 ban

按接口分组：
  组A: daily_basic (3路, ~4000天)
  组B: stk_limit + moneyflow (2+2路, ~4000天)
  组C: margin_detail + hsgt_top10 + ggt_top10 (2+1+1路, ~4000天)
  组D: top_list + top_inst + limit_list (2+2+1路, ~4000天)
  组E: concept_detail (2路, 879次) + index_daily (2路, 200次) + financial (1路, 34期)
  组F: futures + fund (2路, ~5000天)
  组G: major_news (1路, 180天)
"""

import sys, os, time, math, json, threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

import tushare as ts
import pandas as pd
import numpy as np
import calendar
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging, sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
                    stream=sys.stdout)
log = logging.getLogger('MAIN')
# Force flush after every log message
class FlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()
for h in log.handlers:
    log.removeHandler(h)
log.addHandler(FlushHandler(sys.stdout))
log.info("=== LOGGING CONFIGURED ===")

# ─── Config ───
TOKEN = os.environ.get("TUSHARE_TOKEN", "")
if not TOKEN:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('TUSHARE_TOKEN='):
                    TOKEN = line.split('=', 1)[1].strip("'\"")
                    break
ts.set_token(TOKEN)

DB_URL = os.environ.get("QUANT_DB_URL", "postgresql://quant:quant_pass@localhost:5432/quantdb")

AUTO_COLS = {'id', 'asset_id', 'created_at', 'updated_at'}
TS_COLS = {'trade_date', 'cal_date', 'ann_date', 'end_date', 'f_ann_date',
           'list_date', 'delist_date', 'pretrade_date', 'start_date', 'exp_date'}

# ─── Shared Token Bucket Rate Limiter ───
class TokenBucket:
    def __init__(self, rate_per_minute=170):
        self.tokens = rate_per_minute
        self.max_tokens = rate_per_minute
        self.refill_rate = rate_per_minute / 60.0
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens=1, timeout=600):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return 0.0
                wait = (tokens - self.tokens) / self.refill_rate
            time.sleep(min(wait + 0.01, 0.5))
        raise TimeoutError(f"Rate limiter timeout after {timeout}s")

rate_limiter = TokenBucket(195)

# ─── DB Helpers ───
engines_local = threading.local()

def get_engine():
    if not hasattr(engines_local, 'engine') or engines_local.engine is None:
        engines_local.engine = create_engine(
            DB_URL, pool_pre_ping=True, pool_size=3, max_overflow=5
        )
    return engines_local.engine

def get_table_cols(table):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            r = conn.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_name='{table}' ORDER BY ordinal_position"
            ))
            return {row[0]: row[1] for row in r.fetchall()}
    except Exception:
        return {}

col_cache_lock = threading.Lock()
col_cache = {}

def get_table_cols_cached(table):
    with col_cache_lock:
        if table not in col_cache:
            col_cache[table] = get_table_cols(table)
    return col_cache[table]

def bulk_upsert(table, df, pk_cols=None):
    """Robust batch INSERT with smaller batch size and retry"""
    if df is None or df.empty:
        return 0
    df.columns = [c.lower() for c in df.columns]
    col_types = get_table_cols_cached(table)
    existing = set(col_types.keys())
    common = [c for c in df.columns if c in existing and c not in AUTO_COLS]
    if not common:
        return 0
    df = df[common]
    bool_cols = {c for c in common if 'bool' in col_types.get(c, '').lower()}

    quoted_pk = ', '.join(f'"{p}"' for p in pk_cols) if pk_cols else ''
    conflict = f' ON CONFLICT ({quoted_pk}) DO NOTHING' if pk_cols else ''
    cols_str = ', '.join(f'"{c}"' for c in common)

    engine = get_engine()
    total = 0

    # Use small batches to avoid SQL size issues
    batch_size = 100
    for start in range(0, len(df), batch_size):
        batch_df = df.iloc[start:start + batch_size]
        rows_sql = []
        for _, row in batch_df.iterrows():
            vals = []
            for c in common:
                v = row[c]
                if v is None or (isinstance(v, float) and (v != v or math.isinf(v))):
                    vals.append('NULL')
                elif c in TS_COLS and isinstance(v, str) and len(v) == 8 and v.isdigit():
                    s = f'{v[:4]}-{v[4:6]}-{v[6:8]}'
                    vals.append(f"'{s}'::timestamptz")
                elif isinstance(v, str):
                    vals.append(f"'{v.replace(chr(39), chr(39) + chr(39))}'")
                elif isinstance(v, (int, float, np.integer, np.floating)):
                    fv = float(v)
                    if math.isinf(fv) or math.isnan(fv):
                        vals.append('NULL')
                    elif c in bool_cols:
                        vals.append('TRUE' if v else 'FALSE')
                    else:
                        vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append('TRUE' if v else 'FALSE')
                elif isinstance(v, (dict, list)):
                    s = json.dumps(v, ensure_ascii=False)
                    vals.append(f"'{s.replace(chr(39), chr(39) + chr(39))}'")
                else:
                    vals.append(f"'{str(v).replace(chr(39), chr(39) + chr(39))}'")
            rows_sql.append(f'({", ".join(vals)})')

        sql = f'INSERT INTO "{table}" ({cols_str}) VALUES\n' + ',\n'.join(rows_sql) + conflict

        for attempt in range(2):
            try:
                with engine.begin() as conn:
                    conn.execute(text(sql))
                total += len(batch_df)
                break
            except Exception as e:
                if attempt == 0:
                    log.warning(f"  [{table}] batch error (retrying): {str(e)[:150]}")
                    # Retry with half batch
                    half = max(20, len(batch_df) // 2)
                    # Split into two smaller batches
                    count1 = bulk_upsert_small(table, batch_df.iloc[:half], common, cols_str, conflict, bool_cols, engine)
                    count2 = bulk_upsert_small(table, batch_df.iloc[half:], common, cols_str, conflict, bool_cols, engine)
                    total += count1 + count2
                    if count1 + count2 < len(batch_df):
                        log.warning(f"  [{table}] partial insert: {count1 + count2}/{len(batch_df)}")
                    break
                else:
                    log.warning(f"  [{table}] batch failed ({len(batch_df)} rows): {e}")
        if total > 0 and total % 100000 == 0:
            log.info(f"  [{table}] {total:,} rows inserted")
    return total

def bulk_upsert_small(table, batch_df, common, cols_str, conflict, bool_cols, engine):
    """Fallback: insert rows one at a time"""
    total = 0
    for _, row in batch_df.iterrows():
        vals = []
        for c in common:
            v = row[c]
            try:
                if v is None or (isinstance(v, float) and (v != v or math.isinf(v))):
                    vals.append('NULL')
                elif c in TS_COLS and isinstance(v, str) and len(v) == 8 and v.isdigit():
                    s = f'{v[:4]}-{v[4:6]}-{v[6:8]}'
                    vals.append(f"'{s}'::timestamptz")
                elif isinstance(v, str):
                    vals.append(f"'{v.replace(chr(39), chr(39) + chr(39))}'")
                elif isinstance(v, (int, float, np.integer, np.floating)):
                    fv = float(v)
                    if math.isinf(fv) or math.isnan(fv):
                        vals.append('NULL')
                    elif c in bool_cols:
                        vals.append('TRUE' if v else 'FALSE')
                    else:
                        vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append('TRUE' if v else 'FALSE')
                else:
                    vals.append(f"'{str(v).replace(chr(39), chr(39) + chr(39))}'")
            except Exception:
                vals.append('NULL')
        try:
            sql = f'INSERT INTO "{table}" ({cols_str}) VALUES ({", ".join(vals)})' + conflict
            with engine.begin() as conn:
                conn.execute(text(sql))
            total += 1
        except Exception as e2:
            log.warning(f"  [{table}] row insert failed: {str(e2)[:200]}")
    return total

# ─── API Call Wrapper ───
def tushare_call(api_func, *args, **kwargs):
    """Make a rate-limited Tushare API call with retry"""
    rate_limiter.acquire()
    try:
        return api_func(*args, **kwargs)
    except Exception as e:
        estr = str(e)
        if '频率' in estr:
            log.warning(f"  rate limit hit, sleeping 3s")
            time.sleep(3)
            rate_limiter.acquire(2)
            return api_func(*args, **kwargs)
        raise

def pull_by_day_worker(table, api_func, pk_cols, start_date, end_date, fields=None, name=None, max_calls=None):
    """Pull data one day at a time"""
    name = name or table
    fields_arg = fields

    engine = get_engine()
    with engine.connect() as conn:
        trade_dates = pd.read_sql(
            text(f"SELECT cal_date::date FROM ref_trade_cal WHERE exchange='SSE' AND is_open=true AND cal_date >= '{start_date}' AND cal_date <= '{end_date}' ORDER BY cal_date"),
            conn
        )

    dates = [d.strftime('%Y%m%d') for d in trade_dates['cal_date']]
    log.info(f"  [{name}] {len(dates)} trading days to process")

    total = 0
    for i, d in enumerate(dates):
        if max_calls and i >= max_calls:
            break
        try:
            kwargs = {'trade_date': d}
            if fields_arg:
                kwargs['fields'] = fields_arg
            df = tushare_call(api_func, **kwargs)
            if df is not None and not df.empty:
                total += bulk_upsert(table, df, pk_cols)
        except Exception as e:
            if '权限' in str(e):
                log.warning(f"  [{name}] no permission for {d}")
            else:
                log.warning(f"  [{name}] {d}: {e}")

        if total > 0 and total % 100000 == 0:
            log.info(f"  [{name}] {total:,} rows so far")

    log.info(f"  [{name}] DONE: {total:,} rows")
    return total


# ═══════════════════════════════════════
# Pull Functions
# ═══════════════════════════════════════

def worker_daily_basic(progress):
    log.info("== [daily_basic] starting ==")
    r = pull_by_day_worker('raw_daily_basic', ts.pro_api().daily_basic,
                           ['ts_code', 'trade_date'], '20100101', datetime.now().strftime('%Y%m%d'),
                           fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv',
                           name='daily_basic')
    progress['daily_basic'] = {'rows': r, 'done': True}

def worker_stk_limit(progress):
    log.info("== [stk_limit] starting ==")
    r = pull_by_day_worker('raw_stk_limit', ts.pro_api().stk_limit,
                           ['ts_code', 'trade_date'], '20100101', datetime.now().strftime('%Y%m%d'),
                           name='stk_limit')
    progress['stk_limit'] = {'rows': r, 'done': True}

def worker_moneyflow(progress):
    log.info("== [moneyflow] starting ==")
    r = pull_by_day_worker('raw_moneyflow', ts.pro_api().moneyflow,
                           ['ts_code', 'trade_date'], '20100101', datetime.now().strftime('%Y%m%d'),
                           name='moneyflow')
    progress['moneyflow'] = {'rows': r, 'done': True}

def worker_margin(progress):
    log.info("== [margin_detail] starting ==")
    r = pull_by_day_worker('raw_margin_detail', ts.pro_api().margin_detail,
                           ['ts_code', 'trade_date'], '20100101', datetime.now().strftime('%Y%m%d'),
                           name='margin')
    progress['margin'] = {'rows': r, 'done': True}

def worker_hsgt(progress):
    log.info("== [hsgt_top10] starting ==")
    r = pull_by_day_worker('raw_hsgt_top10', ts.pro_api().hsgt_top10,
                           ['trade_date', 'ts_code'], '20141117', datetime.now().strftime('%Y%m%d'),
                           name='hsgt_top10')
    progress['hsgt_top10'] = {'rows': r, 'done': True}

def worker_ggt(progress):
    log.info("== [ggt_top10] starting ==")
    r = pull_by_day_worker('raw_ggt_top10', ts.pro_api().ggt_top10,
                           ['trade_date', 'ts_code'], '20141117', datetime.now().strftime('%Y%m%d'),
                           name='ggt_top10')
    progress['ggt_top10'] = {'rows': r, 'done': True}

def worker_top_list(progress):
    log.info("== [top_list] starting ==")
    r = pull_by_day_worker('raw_top_list', ts.pro_api().top_list,
                           ['trade_date', 'ts_code'], '20100101', datetime.now().strftime('%Y%m%d'),
                           name='top_list')
    progress['top_list'] = {'rows': r, 'done': True}

def worker_top_inst(progress):
    log.info("== [top_inst] starting ==")
    r = pull_by_day_worker('raw_top_inst', ts.pro_api().top_inst,
                           ['trade_date', 'ts_code', 'exalter'], '20100101', datetime.now().strftime('%Y%m%d'),
                           name='top_inst')
    progress['top_inst'] = {'rows': r, 'done': True}

def worker_limit_list(progress):
    log.info("== [limit_list] starting ==")
    r = pull_by_day_worker('raw_limit_list', ts.pro_api().limit_list_d,
                           ['trade_date', 'ts_code'], '20200101', datetime.now().strftime('%Y%m%d'),
                           name='limit_list')
    progress['limit_list'] = {'rows': r, 'done': True}

def worker_concept_detail(progress):
    log.info("== [concept_detail] starting ==")
    engine = get_engine()
    with engine.connect() as conn:
        concepts = pd.read_sql(text("SELECT code, name FROM ref_concept"), conn)

    total = 0
    for _, row in concepts.iterrows():
        try:
            df = tushare_call(ts.pro_api().concept_detail, id=row['code'])
            if df is not None and not df.empty:
                df = df.rename(columns={'id': 'concept_code'})
                total += bulk_upsert('ref_concept_detail', df, ['concept_code', 'ts_code'])
        except Exception as e:
            log.warning(f"  concept {row['code']}: {e}")
        if total > 0 and total % 50000 == 0:
            log.info(f"  [concept_detail] {total:,} rows so far")
    log.info(f"  [concept_detail] DONE: {total:,} rows")
    progress['concept_detail'] = {'rows': total, 'done': True}

def worker_index_daily(progress):
    log.info("== [index_daily] starting ==")
    total = 0
    for mkt in ['SSE', 'SZSE']:
        try:
            df = tushare_call(ts.pro_api().index_basic, market=mkt)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    code = row['ts_code']
                    try:
                        idf = tushare_call(ts.pro_api().index_daily, ts_code=code, start_date='19901219', end_date=datetime.now().strftime('%Y%m%d'))
                        if idf is not None and not idf.empty:
                            total += bulk_upsert('raw_index_daily', idf, ['ts_code', 'trade_date'])
                    except Exception as e:
                        if '权限' not in str(e):
                            log.warning(f"  index {code}: {e}")
        except Exception as e:
            log.warning(f"  index_basic {mkt}: {e}")
    log.info(f"  [index_daily] DONE: {total:,} rows")
    progress['index_daily'] = {'rows': total, 'done': True}

def worker_financial(progress):
    log.info("== [financial] starting ==")
    periods = []
    for y in range(2010, 2027):
        periods.append(f'{y}0630')
        periods.append(f'{y}1231')
    periods = periods[:-1]

    total_reports = 0
    total_indicators = 0

    for api_name in ['income_vip', 'balancesheet_vip', 'cashflow_vip']:
        t = 0
        for p in periods:
            try:
                df = tushare_call(getattr(ts.pro_api(), api_name), period=p)
                if df is not None and not df.empty:
                    t += bulk_upsert('raw_financial_reports', df, ['ts_code', 'end_date'])
            except Exception as e:
                log.warning(f"  {api_name} {p}: {e}")
        log.info(f"  [{api_name}] {t:,} rows")
        total_reports += t

    t = 0
    for p in periods:
        try:
            df = tushare_call(ts.pro_api().fina_indicator_vip, period=p)
            if df is not None and not df.empty:
                t += bulk_upsert('raw_financial_indicators', df, ['ts_code', 'end_date'])
        except Exception as e:
            log.warning(f"  fina_indicator_vip {p}: {e}")
    total_indicators = t
    log.info(f"  [fina_indicator_vip] {t:,} rows")

    for api_name in ['forecast_vip', 'express_vip']:
        t = 0
        for p in periods[-10:]:
            try:
                df = tushare_call(getattr(ts.pro_api(), api_name), period=p)
                if df is not None and not df.empty:
                    t += bulk_upsert('raw_financial_reports', df, ['ts_code', 'end_date'])
            except Exception as e:
                log.warning(f"  {api_name} {p}: {e}")
        log.info(f"  [{api_name}] {t:,} rows")
        total_reports += t

    log.info(f"  [financial] DONE: reports={total_reports:,}, indicators={total_indicators:,}")
    progress['financial'] = {'rows': total_reports, 'indicators': total_indicators, 'done': True}

def worker_futures(progress):
    log.info("== [fut_daily] starting ==")
    r = pull_by_day_worker('raw_fut_daily', ts.pro_api().fut_daily,
                           ['ts_code', 'trade_date'], '20050101', datetime.now().strftime('%Y%m%d'),
                           name='futures')
    progress['futures'] = {'rows': r, 'done': True}

def worker_fund(progress):
    log.info("== [fund_daily] starting ==")
    r = pull_by_day_worker('raw_fund_daily', ts.pro_api().fund_daily,
                           ['ts_code', 'trade_date'], '20050101', datetime.now().strftime('%Y%m%d'),
                           name='fund')
    progress['fund'] = {'rows': r, 'done': True}

def worker_major_news(progress):
    log.info("== [major_news] starting ==")
    total = 0
    for days_ago in range(0, 180):
        d = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
        try:
            df = tushare_call(ts.pro_api().major_news, start_date=d, end_date=d)
            if df is not None and not df.empty:
                total += bulk_upsert('raw_major_news', df, ['news_id'])
        except Exception as e:
            if '权限' in str(e):
                log.warning(f"  major_news: no permission")
                break
            log.warning(f"  major_news {d}: {e}")
        if total > 0 and total % 2000 == 0:
            log.info(f"  [major_news] {total:,} rows so far")
    log.info(f"  [major_news] DONE: {total:,} rows")
    progress['major_news'] = {'rows': total, 'done': True}


# ══════════════════════════════════════
# Main
# ══════════════════════════════════════

if __name__ == '__main__':
    print("=== SCRIPT STARTED ===", flush=True)
    log.info("=" * 60)
    log.info("Tushare 全量拉取 — 并行版本")
    log.info(f"启动时间: {datetime.now()}")
    log.info("限流: 170次/分钟 (共享令牌桶)")
    log.info("=" * 60)

    progress = {}

    # ─── Phase 1: Small tables (serial, fast) ───
    log.info("\n─── Phase 1: Reference & Macro (serial) ───")
    phase1_start = time.time()

    # stock_basic
    log.info("[stock_basic] pulling...")
    df = tushare_call(ts.pro_api().stock_basic,
                      fields='ts_code,symbol,name,area,industry,fullname,market,exchange,curr_type,list_status,list_date,delist_date,is_hs')
    n = bulk_upsert('ref_stock_basic', df, ['ts_code'])
    log.info(f"  done: {n}")

    # trade_cal
    log.info("[trade_cal] pulling...")
    for ex in ['SSE', 'SZSE', 'BSE']:
        df = tushare_call(ts.pro_api().trade_cal, exchange=ex, start_date='19900101', end_date='20261231')
        if df is not None and not df.empty:
            bulk_upsert('ref_trade_cal', df, ['exchange', 'cal_date'])

    # concept
    log.info("[concept] pulling...")
    df = tushare_call(ts.pro_api().concept)
    n = bulk_upsert('ref_concept', df, ['code'])
    log.info(f"  done: {n}")

    # adj_factor
    log.info("[adj_factor] pulling...")
    adj_total = 0
    for y in range(1999, 2027):
        for m in range(1, 13):
            s = f'{y}{m:02d}01'
            e = f'{y}{m:02d}{calendar.monthrange(y, m)[1]:02d}'
            try:
                df = tushare_call(ts.pro_api().adj_factor, start_date=s, end_date=e)
                if df is not None and not df.empty:
                    adj_total += bulk_upsert('ref_adj_factor', df, ['ts_code', 'trade_date'])
            except Exception as ex:
                log.warning(f"  adj_factor {s}: {ex}")
    log.info(f"  adj_factor done: {adj_total:,}")

    # macro
    for api_name, table, pk in [
        ('cn_cpi', 'raw_cn_cpi', ['month']), ('cn_pmi', 'raw_cn_pmi', ['month']),
        ('cn_gdp', 'raw_cn_gdp', ['quarter']), ('cn_m', 'raw_cn_money_supply', ['month']),
        ('shibor', 'raw_shibor', ['date']),
    ]:
        try:
            df = tushare_call(getattr(ts.pro_api(), api_name))
            if df is not None and not df.empty:
                n = bulk_upsert(table, df, pk)
                log.info(f"  [{api_name}] {n:,}")
        except Exception as e:
            log.warning(f"  {api_name}: {e}")

    log.info(f"Phase 1 done in {(time.time()-phase1_start)/60:.1f} min")

    # ─── Phase 2: Parallel bulk pull ───
    log.info("\n─── Phase 2: Parallel bulk pull (15 workers) ───")
    phase2_start = time.time()

    workers = [
        ('daily_basic', worker_daily_basic),
        ('stk_limit', worker_stk_limit),
        ('moneyflow', worker_moneyflow),
        ('margin', worker_margin),
        ('hsgt', worker_hsgt),
        ('ggt', worker_ggt),
        ('top_list', worker_top_list),
        ('top_inst', worker_top_inst),
        ('limit_list', worker_limit_list),
        ('concept_detail', worker_concept_detail),
        ('index_daily', worker_index_daily),
        ('financial', worker_financial),
        ('futures', worker_futures),
        ('fund', worker_fund),
    ]

    with ThreadPoolExecutor(max_workers=14) as executor:
        futures = {executor.submit(fn, progress): name for name, fn in workers}
        done_count = 0
        for fut in as_completed(futures):
            name = futures[fut]
            done_count += 1
            try:
                fut.result()
            except Exception as e:
                log.error(f"  ❌ [{name}] FAILED: {e}")
                import traceback
                log.error(traceback.format_exc())
            elapsed = (time.time() - phase2_start) / 60
            log.info(f"  [{done_count}/{len(workers)}] {name} finished. Elapsed: {elapsed:.1f} min")

    phase2_elapsed = (time.time() - phase2_start) / 60
    log.info(f"Phase 2 done in {phase2_elapsed:.1f} min")

    # ─── Phase 3: Sequential single-worker tasks ───
    log.info("\n─── Phase 3: Sequential (no token contention) ───")
    worker_major_news(progress)
    phase3_elapsed = (time.time() - phase2_start) / 60
    log.info(f"Phase 3 done in {phase3_elapsed:.1f} min")

    # ─── Summary ───
    log.info("\n" + "=" * 60)
    log.info("=== 拉取报告 ===")
    log.info(f"总耗时: {(time.time() - phase1_start)/60:.1f} min")
    for name, p in sorted(progress.items()):
        if isinstance(p, dict):
            rows = p.get('rows', p.get('done', '?'))
            log.info(f"  {name}: {rows:,} 行" if isinstance(rows, int) else f"  {name}: {p}")
    log.info("=" * 60)
