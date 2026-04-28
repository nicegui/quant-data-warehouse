"""
全量数据并行拉取器
- 共享令牌桶限流 180 req/min (留余量)
- 5路并发，不同接口独立推进
- 全部数据填充到空表/半空表
"""
import os, sys, time, math, json, calendar, logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Thread
from queue import Queue

import tushare as ts
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
log = logging.getLogger('MAIN')

# ─── Token ───
TOKEN = os.environ.get("TUSHARE_TOKEN")
if not TOKEN:
    with open('/Users/admin/quant-data-warehouse/.env') as f:
        for line in f:
            if line.startswith('TUSHARE_TOKEN='):
                TOKEN = line.strip().split('=', 1)[1].strip("'\"")
ts.set_token(TOKEN)

DB_URL = "postgresql://quant:quant_pass@localhost:5432/quantdb"
AUTO_COLS = {'id', 'asset_id', 'created_at', 'updated_at'}
TS_DATE_COLS = {'trade_date', 'cal_date', 'ann_date', 'end_date', 'f_ann_date',
                'list_date', 'delist_date', 'pretrade_date', 'start_date', 'exp_date'}

# ═══════════ Rate Limiter ═══════════
class TokenBucket:
    def __init__(self, rate_per_min=180, burst=10):
        self.rate = rate_per_min / 60.0  # per second
        self.burst = burst
        self.tokens = burst
        self.last = time.time()
        self.lock = Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            wait = (1 - self.tokens) / self.rate
            self.tokens = 0
        time.sleep(wait)
        with self.lock:
            self.tokens -= 1

limiter = TokenBucket(rate_per_min=180, burst=10)

# ═══════════ DB Helpers ═══════════
def get_cols(table):
    e = create_engine(DB_URL)
    with e.connect() as c:
        r = c.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'"))
        cols = {row[0]: row[1] for row in r.fetchall()}
    e.dispose()
    return cols

def bulk_insert(table, df, pk_cols=None):
    if df is None or df.empty:
        return 0
    df.columns = [c.lower() for c in df.columns]
    col_types = get_cols(table)
    existing = set(col_types.keys())
    common = [c for c in df.columns if c in existing and c not in AUTO_COLS]
    if not common:
        return 0
    df = df[common]
    bool_c = {c for c in common if 'bool' in col_types.get(c,'').lower()}
    pk = ', '.join(f'"{p}"' for p in pk_cols) if pk_cols else ''
    conflict = f' ON CONFLICT ({pk}) DO NOTHING' if pk_cols else ''
    cols_s = ', '.join(f'"{c}"' for c in common)
    total = 0
    B = 500
    e = create_engine(DB_URL)
    for start in range(0, len(df), B):
        rows = []
        for _, row in df.iloc[start:start+B].iterrows():
            vals = []
            for c in common:
                v = row[c]
                if v is None or (isinstance(v,float) and (v!=v or math.isinf(v))):
                    vals.append('NULL')
                elif c in TS_DATE_COLS and isinstance(v,str) and len(v)==8 and v.isdigit():
                    vals.append(f"'{v[:4]}-{v[4:6]}-{v[6:8]}'::timestamptz")
                elif isinstance(v,str):
                    vals.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(v,(int,float,np.integer,np.floating)):
                    fv = float(v)
                    if math.isinf(fv) or math.isnan(fv):
                        vals.append('NULL')
                    elif c in bool_c:
                        vals.append('TRUE' if v else 'FALSE')
                    else:
                        vals.append(str(v))
                elif isinstance(v,bool):
                    vals.append('TRUE' if v else 'FALSE')
                else:
                    vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
            rows.append(f'({", ".join(vals)})')
        sql = f'INSERT INTO "{table}" ({cols_s}) VALUES\n' + ',\n'.join(rows) + conflict
        with e.begin() as c:
            c.execute(text(sql))
        total += min(B, len(df)-start)
    e.dispose()
    return total

def trade_days(start='19900101'):
    e = create_engine(DB_URL)
    df = pd.read_sql(text(f"SELECT cal_date::date FROM ref_trade_cal WHERE exchange='SSE' AND is_open=true AND cal_date >= '{start[:4]}-{start[4:6]}-{start[6:]}' AND cal_date <= CURRENT_DATE ORDER BY cal_date"), e)
    e.dispose()
    return [d.strftime('%Y%m%d') for d in df['cal_date']]

# ═══════════ Pull Workers ═══════════

def pull_daily_basic():
    lg = logging.getLogger('daily_basic')
    lg.info("开始拉取...")
    pro = ts.pro_api()
    total = 0
    for d in trade_days('20100101'):
        limiter.acquire()
        try:
            df = pro.daily_basic(trade_date=d,
                fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv')
            if df is not None and not df.empty:
                total += bulk_insert('raw_daily_basic', df, ['ts_code','trade_date'])
        except Exception as e:
            lg.warning(f"{d}: {e}")
            time.sleep(2)
    lg.info(f"完成! {total:,} rows")

def pull_stk_limit():
    lg = logging.getLogger('stk_limit')
    lg.info("开始拉取...")
    pro = ts.pro_api()
    total = 0
    for d in trade_days('20100101'):
        limiter.acquire()
        try:
            df = pro.stk_limit(trade_date=d)
            if df is not None and not df.empty:
                total += bulk_insert('raw_stk_limit', df, ['ts_code','trade_date'])
        except Exception as e:
            lg.warning(f"{d}: {e}")
            time.sleep(2)
    lg.info(f"完成! {total:,} rows")

def pull_moneyflow():
    lg = logging.getLogger('moneyflow')
    lg.info("开始拉取...")
    pro = ts.pro_api()
    total = 0
    for d in trade_days('20100101'):
        limiter.acquire()
        try:
            df = pro.moneyflow(trade_date=d)
            if df is not None and not df.empty:
                total += bulk_insert('raw_moneyflow', df, ['ts_code','trade_date'])
        except Exception as e:
            lg.warning(f"{d}: {e}")
            time.sleep(2)
    lg.info(f"完成! {total:,} rows")

def pull_margin():
    lg = logging.getLogger('margin')
    lg.info("开始拉取...")
    pro = ts.pro_api()
    total = 0
    for d in trade_days('20100101'):
        limiter.acquire()
        try:
            df = pro.margin_detail(trade_date=d)
            if df is not None and not df.empty:
                total += bulk_insert('raw_margin_detail', df, ['ts_code','trade_date'])
        except Exception as e:
            lg.warning(f"{d}: {e}")
            time.sleep(2)
    lg.info(f"完成! {total:,} rows")

def pull_hsgt():
    lg = logging.getLogger('hsgt_ggt')
    lg.info("开始拉取北向/南向...")
    pro = ts.pro_api()
    t1 = t2 = 0
    for d in trade_days('20141117'):
        limiter.acquire()
        try:
            df = pro.hsgt_top10(trade_date=d)
            if df is not None and not df.empty:
                t1 += bulk_insert('raw_hsgt_top10', df)
        except: pass
        limiter.acquire()
        try:
            df = pro.ggt_top10(trade_date=d)
            if df is not None and not df.empty:
                t2 += bulk_insert('raw_ggt_top10', df)
        except: pass
    lg.info(f"完成! hsgt={t1}, ggt={t2}")

def pull_top():
    lg = logging.getLogger('top_list')
    lg.info("开始拉取龙虎榜...")
    pro = ts.pro_api()
    t1 = t2 = t3 = 0
    for d in trade_days('20100101'):
        limiter.acquire()
        try:
            df = pro.top_list(trade_date=d)
            if df is not None and not df.empty:
                t1 += bulk_insert('raw_top_list', df, ['trade_date','ts_code'])
        except: pass
        limiter.acquire()
        try:
            df = pro.top_inst(trade_date=d)
            if df is not None and not df.empty:
                t2 += bulk_insert('raw_top_inst', df, ['trade_date','ts_code','exalter'])
        except: pass
    # limit_list from 2020
    for d in trade_days('20200101'):
        limiter.acquire()
        try:
            df = pro.limit_list_d(trade_date=d)
            if df is not None and not df.empty:
                t3 += bulk_insert('raw_limit_list', df, ['trade_date','ts_code'])
        except: pass
    lg.info(f"完成! top_list={t1}, top_inst={t2}, limit_list={t3}")

def pull_index():
    lg = logging.getLogger('index_daily')
    lg.info("开始拉取指数日线...")
    pro = ts.pro_api()
    total = 0
    for mkt in ['SSE','SZSE']:
        limiter.acquire()
        idx_df = pro.index_basic(market=mkt)
        if idx_df is None or idx_df.empty:
            continue
        for _, row in idx_df.iterrows():
            code = row['ts_code']
            limiter.acquire()
            try:
                df = pro.index_daily(ts_code=code, start_date='19901219', end_date=datetime.now().strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    total += bulk_insert('raw_index_daily', df, ['ts_code','trade_date'])
            except Exception as e:
                if '权限' not in str(e):
                    lg.warning(f"{code}: {e}")
    lg.info(f"完成! {total:,} rows")

def pull_concept_detail():
    lg = logging.getLogger('concept_detail')
    lg.info("开始拉取概念成分股...")
    pro = ts.pro_api()
    e = create_engine(DB_URL)
    concepts = pd.read_sql(text("SELECT code FROM ref_concept"), e)
    e.dispose()
    total = 0
    for _, row in concepts.iterrows():
        limiter.acquire()
        try:
            df = pro.concept_detail(id=row['code'])
            if df is not None and not df.empty:
                df = df.rename(columns={'id': 'concept_code'})
                total += bulk_insert('ref_concept_detail', df, ['concept_code','ts_code'])
        except Exception as e:
            lg.warning(f"{row['code']}: {e}")
    lg.info(f"完成! {total:,} rows")

def pull_financial():
    lg = logging.getLogger('financial')
    lg.info("开始拉取财报...")
    pro = ts.pro_api()
    periods = []
    for y in range(2010, 2027):
        periods.append(f'{y}0630')
        periods.append(f'{y}1231')
    periods = periods[:-1]
    
    r1 = r2 = r3 = 0
    for api_name in ['income_vip','balancesheet_vip','cashflow_vip']:
        for p in periods:
            limiter.acquire()
            try:
                df = getattr(pro, api_name)(period=p)
                if df is not None and not df.empty:
                    r1 += bulk_insert('raw_financial_reports', df, ['ts_code','end_date','report_type'])
            except Exception as e:
                lg.warning(f"{api_name} {p}: {e}")
                time.sleep(3)
        lg.info(f"  {api_name}: {r1:,}")
    
    for p in periods:
        limiter.acquire()
        try:
            df = pro.fina_indicator_vip(period=p)
            if df is not None and not df.empty:
                r2 += bulk_insert('raw_financial_indicators', df, ['ts_code','end_date'])
        except Exception as e:
            lg.warning(f"fina_indicator {p}: {e}")
            time.sleep(3)
    lg.info(f"  fina_indicator: {r2:,}")
    
    for api_name in ['forecast_vip','express_vip']:
        for p in periods[-10:]:
            limiter.acquire()
            try:
                df = getattr(pro, api_name)(period=p)
                if df is not None and not df.empty:
                    r3 += bulk_insert('raw_financial_reports', df)
            except: pass
        lg.info(f"  {api_name}: {r3:,}")
    lg.info(f"完成! reports={r1}, indicators={r2}, forecast={r3}")

def pull_fut_fund():
    lg = logging.getLogger('fut_fund')
    lg.info("开始拉取期货/基金日线...")
    pro = ts.pro_api()
    t1 = t2 = 0
    for d in trade_days('20050101'):
        limiter.acquire()
        try:
            df = pro.fut_daily(trade_date=d)
            if df is not None and not df.empty:
                t1 += bulk_insert('raw_fut_daily', df, ['ts_code','trade_date'])
        except: pass
        limiter.acquire()
        try:
            df = pro.fund_daily(trade_date=d)
            if df is not None and not df.empty:
                t2 += bulk_insert('raw_fund_daily', df, ['ts_code','trade_date'])
        except: pass
    lg.info(f"完成! fut={t1:,}, fund={t2:,}")

def pull_major_news():
    lg = logging.getLogger('major_news')
    lg.info("开始拉取重大新闻...")
    pro = ts.pro_api()
    total = 0
    for i in range(180):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        limiter.acquire()
        try:
            df = pro.major_news(start_date=d, end_date=d)
            if df is not None and not df.empty:
                total += bulk_insert('raw_major_news', df)
        except Exception as e:
            lg.warning(f"{d}: {e}")
    lg.info(f"完成! {total:,} rows")

# ═══════════ Runner ═══════════
WORKERS = [
    ("daily_basic",      pull_daily_basic),
    ("stk_limit",        pull_stk_limit),
    ("moneyflow",        pull_moneyflow),
    ("margin+hsgt+ggt",  pull_margin),      # margin + hsgt done in sequence 
    ("top_list/inst",    pull_top),
    ("index_daily",      pull_index),
    ("concept_detail",   pull_concept_detail),
    ("financial",        pull_financial),
    ("fut+fund",         pull_fut_fund),
    ("major_news",       pull_major_news),
]

# Actually let me merge some to reduce thread count
# 5 threads is cleaner given the shared rate limiter
WORKERS_5 = [
    ("A: daily_basic",       pull_daily_basic),
    ("B: stk_limit+moneyflow", lambda: [pull_stk_limit(), pull_moneyflow()]),
    ("C: margin+hsgt+ggt",   lambda: [pull_margin(), pull_hsgt()]),
    ("D: top_list+index",    lambda: [pull_top(), pull_index()]),
    ("E: concept+finance+fut+news", lambda: [pull_concept_detail(), pull_financial(), pull_fut_fund(), pull_major_news()]),
]

if __name__ == '__main__':
    t0 = time.time()
    log.info("="*60)
    log.info("全量并行拉取开始 (5路并发, 180 req/min)")
    log.info("="*60)
    
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fn): name for name, fn in WORKERS_5}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                result = fut.result()
                log.info(f"[{name}] 线程完成")
            except Exception as e:
                log.error(f"[{name}] 异常: {e}")
    
    elapsed = time.time() - t0
    log.info(f"\n{'='*60}")
    log.info(f"全部完成! 耗时 {elapsed/60:.1f} 分钟")
    log.info(f"{'='*60}")
