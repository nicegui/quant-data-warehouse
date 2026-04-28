"""逐个测通 Tushare 数据接口
测试并写入数据库，记录结果
"""
import tushare as ts, os, time, math, calendar, logging
from datetime import datetime
from typing import Optional
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# Token
token = None
with open('/Users/admin/quant-data-warehouse/.env') as f:
    for line in f:
        if line.startswith('TUSHARE_TOKEN='):
            token = line.strip().split('=', 1)[1].strip("'\"")
ts.set_token(token)
pro = ts.pro_api()

engine = create_engine("postgresql://quant:quant_pass@localhost:5432/quantdb",
                       pool_pre_ping=True, pool_size=5)

AUTO_COLS = {'id', 'asset_id', 'created_at', 'updated_at'}
TS_COLS = {'trade_date', 'cal_date', 'ann_date', 'end_date', 'f_ann_date', 'list_date', 'delist_date', 'pretrade_date', 'start_date', 'exp_date'}

def get_table_cols(table):
    with engine.connect() as conn:
        r = conn.execute(text(f"""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name='{table}' ORDER BY ordinal_position
        """))
        return {row[0]: row[1] for row in r.fetchall()}

def bulk_upsert(table, df, pk_cols=None, batch=500):
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
    
    conflict = ''
    if pk_cols:
        quoted = ', '.join(f'"{p}"' for p in pk_cols)
        conflict = f' ON CONFLICT ({quoted}) DO NOTHING'
    
    cols_str = ', '.join(f'"{c}"' for c in common)
    total = 0
    
    for start in range(0, len(df), batch):
        batch_df = df.iloc[start:start+batch]
        all_vals = []
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
                    if isinstance(v, float) and (math.isinf(float(v)) or math.isnan(float(v))):
                        vals.append('NULL')
                    else:
                        vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append('TRUE' if v else 'FALSE')
                else:
                    vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
            all_vals.append(f'({", ".join(vals)})')
        
        sql = f'INSERT INTO "{table}" ({cols_str}) VALUES\n' + ',\n'.join(all_vals) + conflict
        with engine.begin() as conn:
            conn.execute(text(sql))
        total += len(batch_df)
    return total

def test_pull(name, table, api_func, pk_cols, is_monthly=False, **kwargs):
    """Test an API: call it, upsert into table, report"""
    log.info(f"\n{'='*50}")
    log.info(f"▶ {name} → {table}")
    
    # Check current
    try:
        cur = pd.read_sql(text(f'SELECT COUNT(*) FROM "{table}"'), engine).iloc[0,0]
        log.info(f"  当前: {cur:,} rows")
    except:
        cur = 0
        log.info(f"  表不存在?")
    
    if is_monthly:
        # Monthly bulk pull
        total = 0
        for y in range(kwargs.get('start_year', 1990), kwargs.get('end_year', 2027)):
            for m in range(1, 13):
                if y == kwargs.get('start_year', 1990) and m < kwargs.get('start_month', 1):
                    continue
                if y == kwargs.get('end_year', 2027) and m > kwargs.get('end_month', 12):
                    continue
                s = f'{y}{m:02d}01'
                last = calendar.monthrange(y, m)[1]
                e = f'{y}{m:02d}{last:02d}'
                try:
                    df = api_func(start_date=s, end_date=e, **{k:v for k,v in kwargs.items() if k not in ['start_year','start_month','end_year','end_month']})
                    time.sleep(0.15)
                    if df is not None and not df.empty:
                        total += bulk_upsert(table, df, pk_cols)
                except Exception as ex:
                    if '频率' in str(ex):
                        time.sleep(3)
                    else:
                        log.warning(f"    {s}: {ex}")
                        time.sleep(1)
            if y % 5 == 0:
                log.info(f"  [{name}] {y}: cumulative {total}")
        log.info(f"  [{name}] done: {total}")
    else:
        # Single test
        try:
            df = api_func(**kwargs)
            time.sleep(0.3)
            if df is not None and not df.empty:
                n = bulk_upsert(table, df, pk_cols)
                log.info(f"  ✅ API OK: {len(df)} rows, inserted {n}")
                log.info(f"  📋 Fields: {list(df.columns)[:8]}...")
            else:
                log.info(f"  ⚠️  Empty result")
        except Exception as e:
            log.error(f"  ❌ {e}")
    
    after = pd.read_sql(text(f'SELECT COUNT(*) FROM "{table}"'), engine).iloc[0,0]
    log.info(f"  现在: {after:,} rows (+{after-cur})")
    return after - cur

# ══════════════════════════════════════
# 1. daily_basic (基本面/估值)
# ══════════════════════════════════════
log.info("\n\n========== 1. daily_basic ==========")
test_pull("daily_basic_test", "raw_daily_basic", pro.daily_basic, 
          ['ts_code', 'trade_date'],
          trade_date='20260427',
          fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv')

# ══════════════════════════════════════
# 2. index_daily (指数日线)
# ══════════════════════════════════════
log.info("\n\n========== 2. index_daily ==========")
# Need to get index list first
idx_df = pro.index_basic(market='SSE')
log.info(f"  SSE indices: {len(idx_df)}")
time.sleep(0.3)

# Test with main indices
for idx in ['000001.SH', '000300.SH', '000016.SH', '000688.SH']:
    try:
        df = pro.index_daily(ts_code=idx, start_date='20260401', end_date='20260427')
        time.sleep(0.15)
        if df is not None and not df.empty:
            n = bulk_upsert('raw_index_daily', df, ['ts_code', 'trade_date'])
            log.info(f"  {idx}: {len(df)} rows, inserted {n}")
    except Exception as e:
        log.warning(f"  {idx}: {e}")

# ══════════════════════════════════════
# 3. moneyflow (资金流向)
# ══════════════════════════════════════
log.info("\n\n========== 3. moneyflow ==========")
test_pull("moneyflow_test", "raw_moneyflow", pro.moneyflow,
          ['ts_code', 'trade_date'],
          trade_date='20260427')

# ══════════════════════════════════════
# 4. stk_limit (涨跌停限制)
# ══════════════════════════════════════
log.info("\n\n========== 4. stk_limit ==========")
test_pull("stk_limit_test", "raw_stk_limit", pro.stk_limit,
          ['ts_code', 'trade_date'],
          trade_date='20260427')

# ══════════════════════════════════════
# 5. 北向/南向资金
# ══════════════════════════════════════
log.info("\n\n========== 5. HSGT/GGT ==========")
test_pull("hsgt_top10", "raw_hsgt_top10", pro.hsgt_top10,
          None, trade_date='20260427')
test_pull("ggt_top10", "raw_ggt_top10", pro.ggt_top10,
          None, trade_date='20260427')

# ══════════════════════════════════════
# 6. margin (融资融券)
# ══════════════════════════════════════
log.info("\n\n========== 6. margin ==========")
test_pull("margin_detail", "raw_margin_detail", pro.margin_detail,
          ['ts_code', 'trade_date'],
          trade_date='20260427')

# ══════════════════════════════════════
# 7. 龙虎榜
# ══════════════════════════════════════
log.info("\n\n========== 7. Dragon & Tiger ==========")
test_pull("top_list", "raw_top_list", pro.top_list,
          ['trade_date', 'ts_code'],
          trade_date='20260427')
test_pull("top_inst", "raw_top_inst", pro.top_inst,
          ['trade_date', 'ts_code', 'exalter'],
          trade_date='20260427')

# ══════════════════════════════════════
# 8. 涨停列表
# ══════════════════════════════════════
log.info("\n\n========== 8. limit_list ==========")
test_pull("limit_list_d", "raw_limit_list", pro.limit_list_d,
          ['trade_date', 'ts_code'],
          trade_date='20260427')

# ══════════════════════════════════════
# 9. 概念明细
# ══════════════════════════════════════
log.info("\n\n========== 9. concept_detail ==========")
try:
    concepts = pd.read_sql(text('SELECT code FROM ref_concept LIMIT 5'), engine)
    for _, row in concepts.iterrows():
        try:
            df = pro.concept_detail(id=row['code'])
            time.sleep(0.2)
            if df is not None and not df.empty:
                n = bulk_upsert('ref_concept_detail', df, ['id', 'ts_code'])
                log.info(f"  concept {row['code']}: {len(df)} rows, inserted {n}")
        except Exception as e:
            log.warning(f"  concept {row['code']}: {e}")
except Exception as e:
    log.warning(f"  concepts: {e}")

# ══════════════════════════════════════
# 10. 重大新闻
# ══════════════════════════════════════
log.info("\n\n========== 10. major_news ==========")
test_pull("major_news", "raw_major_news", pro.major_news,
          None,
          start_date='20260420', end_date='20260427')

# ══════════════════════════════════════
# 11. 期货/基金日线
# ══════════════════════════════════════
log.info("\n\n========== 11. futures & fund ==========")
test_pull("fut_daily", "raw_fut_daily", pro.fut_daily,
          ['ts_code', 'trade_date'],
          trade_date='20260427')
test_pull("fund_daily", "raw_fund_daily", pro.fund_daily,
          ['ts_code', 'trade_date'],
          trade_date='20260427')

# ══════════════════════════════════════
# 12. 财务接口
# ══════════════════════════════════════
log.info("\n\n========== 12. Financial VIP ==========")
for api_name in ['income_vip', 'balancesheet_vip', 'cashflow_vip']:
    try:
        df = getattr(pro, api_name)(period='20251231')
        time.sleep(0.3)
        if df is not None and not df.empty:
            n = bulk_upsert('raw_financial_reports', df, ['ts_code', 'end_date', 'report_type'])
            log.info(f"  {api_name}: {len(df)} rows, inserted {n}")
    except Exception as e:
        log.warning(f"  {api_name}: {e}")

# fina_indicator_vip
try:
    df = pro.fina_indicator_vip(period='20251231')
    time.sleep(0.3)
    if df is not None and not df.empty:
        n = bulk_upsert('raw_financial_indicators', df, ['ts_code', 'end_date'])
        log.info(f"  fina_indicator_vip: {len(df)} rows, inserted {n}")
except Exception as e:
    log.warning(f"  fina_indicator_vip: {e}")

# ══════════════════════════════════════
# 总结
# ══════════════════════════════════════
log.info("\n\n========== SUMMARY ==========")
tables_to_check = [
    'raw_daily_basic', 'raw_index_daily', 'raw_moneyflow', 'raw_stk_limit',
    'raw_hsgt_top10', 'raw_ggt_top10', 'raw_margin_detail',
    'raw_top_list', 'raw_top_inst', 'raw_limit_list',
    'ref_concept_detail', 'raw_major_news',
    'raw_fut_daily', 'raw_fund_daily',
    'raw_financial_reports', 'raw_financial_indicators'
]
for tbl in tables_to_check:
    try:
        cnt = pd.read_sql(text(f'SELECT COUNT(*) FROM "{tbl}"'), engine).iloc[0,0]
        log.info(f"  {tbl}: {cnt:,} rows")
    except:
        log.info(f"  {tbl}: TABLE NOT FOUND")
