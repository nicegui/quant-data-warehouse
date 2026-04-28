"""
Tushare 全量历史数据拉取脚本 V2
接口全部测通+修复方案：
- daily_basic/moneyflow/margin/stk_limit → 按天拉（解决6000行截断）
- index_daily → 逐指数拉
- 新增: hsgt_top10, ggt_top10, top_list, top_inst, limit_list, major_news, concept_detail
- 批量 INSERT 替代行级 INSERT（10x 速度提升）
"""
import os, sys, time, math, json, calendar, logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import tushare as ts
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ─── Config ───
TOKEN = os.environ.get("TUSHARE_TOKEN")
if not TOKEN:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    with open(env_path) as f:
        for line in f:
            if line.startswith('TUSHARE_TOKEN='):
                TOKEN = line.strip().split('=', 1)[1].strip("'\"")
ts.set_token(TOKEN)

DB_URL = os.environ.get("QUANT_DB_URL", "postgresql://quant:quant_pass@localhost:5432/quantdb")

AUTO_COLS = {'id', 'asset_id', 'created_at', 'updated_at'}
TS_COLS = {'trade_date', 'cal_date', 'ann_date', 'end_date', 'f_ann_date',
           'list_date', 'delist_date', 'pretrade_date', 'start_date', 'exp_date'}

def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

def table_count(table):
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text(f'SELECT count(*) FROM "{table}"'))
        c = r.scalar() or 0
    engine.dispose()
    return c

def get_table_cols(table):
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text(f"""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name='{table}' ORDER BY ordinal_position
        """))
        cols = {row[0]: row[1] for row in r.fetchall()}
    engine.dispose()
    return cols

def bulk_upsert(table, df, pk_cols=None, batch=500):
    """Batch INSERT with ON CONFLICT DO NOTHING"""
    if df is None or df.empty:
        return 0
    df.columns = [c.lower() for c in df.columns]
    
    col_types = get_table_cols(table)
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
    for start in range(0, len(df), batch):
        batch_df = df.iloc[start:start+batch]
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
                    vals.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(v, (int, float, np.integer, np.floating)):
                    if isinstance(float(v), float) and (math.isinf(float(v)) or math.isnan(float(v))):
                        vals.append('NULL')
                    elif c in bool_cols:
                        vals.append('TRUE' if v else 'FALSE')
                    else:
                        vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append('TRUE' if v else 'FALSE')
                elif isinstance(v, (dict, list)):
                    s = json.dumps(v, ensure_ascii=False)
                    vals.append(f"'{s.replace(chr(39), chr(39)+chr(39))}'")
                else:
                    vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
            rows_sql.append(f'({", ".join(vals)})')
        
        sql = f'INSERT INTO "{table}" ({cols_str}) VALUES\n' + ',\n'.join(rows_sql) + conflict
        with engine.begin() as conn:
            conn.execute(text(sql))
        total += len(batch_df)
    engine.dispose()
    return total

def pull_by_day(table, api_func, pk_cols, start_date='20100101', end_date=None, rate=0.15, **kwargs):
    """Pull data one day at a time (solves 6000-row limit)"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    engine_tmp = get_engine()
    trade_dates = pd.read_sql(
        text(f"SELECT cal_date::date FROM ref_trade_cal WHERE exchange='SSE' AND is_open=true AND cal_date >= '{start_date}' AND cal_date <= '{end_date}' ORDER BY cal_date"),
        engine_tmp
    )
    engine_tmp.dispose()
    
    dates = [d.strftime('%Y%m%d') for d in trade_dates['cal_date']]
    log.info(f"  [{table}] {len(dates)} trading days to process")
    
    total = 0
    for d in dates:
        try:
            df = api_func(trade_date=d, **kwargs)
            time.sleep(rate)
            if df is not None and not df.empty:
                total += bulk_upsert(table, df, pk_cols)
        except Exception as e:
            if '频率' in str(e):
                time.sleep(3)
            else:
                log.warning(f"    {d}: {e}")
                time.sleep(1)
        if total > 0 and total % 50000 == 0:
            log.info(f"    [{table}] {total:,} rows so far")
    log.info(f"  [{table}] done: {total:,} rows")
    return total

# ═══════════════════════════════════════
# Pull Functions
# ═══════════════════════════════════════

def pull_stock_basic():
    log.info("[stock_basic] pulling...")
    df = ts.pro_api().stock_basic(
        fields='ts_code,symbol,name,area,industry,fullname,market,exchange,curr_type,list_status,list_date,delist_date,is_hs')
    n = bulk_upsert('ref_stock_basic', df, ['ts_code'])
    log.info(f"  done: {n}")

def pull_trade_cal():
    log.info("[trade_cal] pulling...")
    all_dfs = []
    for ex in ['SSE', 'SZSE', 'BSE']:
        df = ts.pro_api().trade_cal(exchange=ex, start_date='19900101', end_date='20261231')
        if df is not None and not df.empty:
            all_dfs.append(df)
        time.sleep(0.2)
    if all_dfs:
        df = pd.concat(all_dfs)
        n = bulk_upsert('ref_trade_cal', df, ['exchange', 'cal_date'])
        log.info(f"  done: {n}")

def pull_concept():
    log.info("[concept] pulling...")
    df = ts.pro_api().concept()
    n = bulk_upsert('ref_concept', df, ['code'])
    log.info(f"  done: {n}")

def pull_concept_detail():
    """所有概念的成分股"""
    log.info("[concept_detail] pulling...")
    concepts = pd.read_sql(text("SELECT code, name FROM ref_concept"), get_engine())
    total = 0
    for _, row in concepts.iterrows():
        try:
            df = ts.pro_api().concept_detail(id=row['code'])
            time.sleep(0.12)
            if df is not None and not df.empty:
                # Map API columns to table columns
                df = df.rename(columns={'id': 'concept_code'})
                total += bulk_upsert('ref_concept_detail', df, ['concept_code', 'ts_code'])
        except Exception as e:
            log.warning(f"  concept {row['code']}: {e}")
    log.info(f"  done: {total}")

def pull_adj_factor():
    log.info("[adj_factor] pulling full history...")
    total = 0
    for y, m in [(y,m) for y in range(1999,2027) for m in range(1,13)]:
        import calendar
        s = f'{y}{m:02d}01'
        e = f'{y}{m:02d}{calendar.monthrange(y,m)[1]:02d}'
        try:
            df = ts.pro_api().adj_factor(start_date=s, end_date=e)
            time.sleep(0.12)
            if df is not None and not df.empty:
                total += bulk_upsert('ref_adj_factor', df, ['ts_code', 'trade_date'])
        except Exception as e:
            log.warning(f"  adj_factor {s}: {e}")
            time.sleep(3)
    log.info(f"  done: {total:,}")

def pull_daily_basic():
    log.info("[daily_basic] pulling all days (2010-2026)...")
    pull_by_day('raw_daily_basic', ts.pro_api().daily_basic, ['ts_code', 'trade_date'],
                '20100101', None, 0.15,
                fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv')
    # NOTE: daily_basic API without ts_code returns all stocks for a day (fits in one call)
    # But it might hit limit for days with 5000+ stocks. If so, remove ts_code='' param.
    # Tushare's daily_basic actually doesn't require ts_code for bulk pull

def pull_index_daily():
    """按指数逐个拉全量历史"""
    log.info("[index_daily] pulling...")
    # Get all indices
    idx_dfs = []
    for mkt in ['SSE', 'SZSE']:
        df = ts.pro_api().index_basic(market=mkt)
        time.sleep(0.3)
        if df is not None and not df.empty:
            idx_dfs.append(df)
    all_idx = pd.concat(idx_dfs)
    log.info(f"  {len(all_idx)} indices")
    
    total = 0
    for _, row in all_idx.iterrows():
        code = row['ts_code']
        try:
            df = ts.pro_api().index_daily(ts_code=code, start_date='19901219', end_date=datetime.now().strftime('%Y%m%d'))
            time.sleep(0.15)
            if df is not None and not df.empty:
                total += bulk_upsert('raw_index_daily', df, ['ts_code', 'trade_date'])
        except Exception as e:
            if '权限' in str(e):
                log.warning(f"  {code}: no permission")
            else:
                log.warning(f"  {code}: {e}")
        if total > 0 and total % 500000 == 0:
            log.info(f"    [{total:,}] rows so far")
    log.info(f"  done: {total:,}")

def pull_stk_limit():
    log.info("[stk_limit] pulling all days...")
    pull_by_day('raw_stk_limit', ts.pro_api().stk_limit, ['ts_code', 'trade_date'],
                '20100101', None, 0.15)

def pull_moneyflow():
    log.info("[moneyflow] pulling all days...")
    pull_by_day('raw_moneyflow', ts.pro_api().moneyflow, ['ts_code', 'trade_date'],
                '20100101', None, 0.15)

def pull_margin():
    log.info("[margin_detail] pulling all days...")
    pull_by_day('raw_margin_detail', ts.pro_api().margin_detail, ['ts_code', 'trade_date'],
                '20100101', None, 0.15)

def pull_hsgt_top10():
    log.info("[hsgt_top10] pulling all days (2014-2026)...")
    pull_by_day('raw_hsgt_top10', ts.pro_api().hsgt_top10, None,
                '20141117', None, 0.15)

def pull_ggt_top10():
    log.info("[ggt_top10] pulling all days (2014-2026)...")
    pull_by_day('raw_ggt_top10', ts.pro_api().ggt_top10, None,
                '20141117', None, 0.15)

def pull_top_list():
    log.info("[top_list] pulling all days...")
    pull_by_day('raw_top_list', ts.pro_api().top_list, ['trade_date', 'ts_code'],
                '20100101', None, 0.2)

def pull_top_inst():
    log.info("[top_inst] pulling all days...")
    pull_by_day('raw_top_inst', ts.pro_api().top_inst, ['trade_date', 'ts_code', 'exalter'],
                '20100101', None, 0.2)

def pull_limit_list():
    log.info("[limit_list] pulling all days...")
    pull_by_day('raw_limit_list', ts.pro_api().limit_list_d, ['trade_date', 'ts_code'],
                '20200101', None, 0.2)

def pull_major_news():
    log.info("[major_news] pulling...")
    total = 0
    for days_ago in range(0, 180):
        d = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
        try:
            df = ts.pro_api().major_news(start_date=d, end_date=d)
            time.sleep(0.15)
            if df is not None and not df.empty:
                total += bulk_upsert('raw_major_news', df)
        except Exception as e:
            log.warning(f"  {d}: {e}")
    log.info(f"  done: {total}")

def pull_financial():
    log.info("[financial] pulling full history...")
    periods = []
    for y in range(2010, 2027):
        periods.append(f'{y}0630')
        periods.append(f'{y}1231')
    periods = periods[:-1]
    
    for api_name in ['income_vip', 'balancesheet_vip', 'cashflow_vip']:
        t = 0
        for p in periods:
            try:
                df = getattr(ts.pro_api(), api_name)(period=p)
                time.sleep(0.2)
                if df is not None and not df.empty:
                    t += bulk_upsert('raw_financial_reports', df, ['ts_code', 'end_date', 'report_type'])
            except Exception as e:
                log.warning(f"  {api_name} {p}: {e}")
                time.sleep(3)
        log.info(f"  [{api_name}] {t:,}")
    
    # fina_indicator_vip
    fi = 0
    for p in periods:
        try:
            df = ts.pro_api().fina_indicator_vip(period=p)
            time.sleep(0.2)
            if df is not None and not df.empty:
                fi += bulk_upsert('raw_financial_indicators', df, ['ts_code', 'end_date'])
        except Exception as e:
            log.warning(f"  fina_indicator_vip {p}: {e}")
            time.sleep(3)
    log.info(f"  [fina_indicator_vip] {fi:,}")
    
    # forecast/express (近5年)
    for api_name in ['forecast_vip', 'express_vip']:
        t = 0
        for p in periods[-10:]:
            try:
                df = getattr(ts.pro_api(), api_name)(period=p)
                time.sleep(0.2)
                if df is not None and not df.empty:
                    t += bulk_upsert('raw_financial_reports', df)
            except Exception as e:
                log.warning(f"  {api_name} {p}: {e}")
        log.info(f"  [{api_name}] {t:,}")

def pull_macro():
    for api_name, table in [
        ('cn_cpi', 'raw_cn_cpi'), ('cn_pmi', 'raw_cn_pmi'), ('cn_gdp', 'raw_cn_gdp'),
        ('cn_m', 'raw_cn_money_supply'), ('shibor', 'raw_shibor'),
    ]:
        try:
            df = getattr(ts.pro_api(), api_name)()
            time.sleep(0.2)
            if df is not None and not df.empty:
                n = bulk_upsert(table, df)
                log.info(f"  [{api_name}] {n:,}")
        except Exception as e:
            log.warning(f"  {api_name}: {e}")

def pull_futures():
    log.info("[fut_daily] pulling...")
    pull_by_day('raw_fut_daily', ts.pro_api().fut_daily, ['ts_code', 'trade_date'],
                '20050101', None, 0.15)

def pull_fund():
    log.info("[fund_daily] pulling...")
    pull_by_day('raw_fund_daily', ts.pro_api().fund_daily, ['ts_code', 'trade_date'],
                '20050101', None, 0.15)

# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

if __name__ == '__main__':
    log.info("=== Tushare Full History Pull (V2) ===")
    
    # Reference (small)
    pull_stock_basic()
    pull_trade_cal()
    pull_concept()
    pull_concept_detail()
    pull_adj_factor()
    
    # Index & macro (small-medium)
    pull_index_daily()
    pull_macro()
    
    # Market data (按天拉，无6000行限制)
    pull_daily_basic()
    pull_stk_limit()
    
    # Money flow
    pull_moneyflow()
    pull_margin()
    pull_hsgt_top10()
    pull_ggt_top10()
    
    # Dragon & tiger
    pull_top_list()
    pull_top_inst()
    pull_limit_list()
    
    # News
    pull_major_news()
    
    # Financial
    pull_financial()
    
    # Futures & fund
    pull_futures()
    pull_fund()
    
    log.info("=== ALL DONE! ===")
