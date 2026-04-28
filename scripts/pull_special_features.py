#!/usr/bin/env python3
"""拉取 Tushare 特色数据: report_rc, cyq_perf, cyq_chips, broker_recommend"""
import sys, os, time, math
import pandas as pd
import tushare as ts
from sqlalchemy import text, create_engine
import psycopg2

sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Read token
env_path = os.path.expanduser('~/quant-data-warehouse/.env')
token = None
with open(env_path) as f:
    for line in f:
        if line.startswith('TUSHARE_TOKEN='):
            token = line.strip().split('=', 1)[1].strip()
            break

ts.set_token(token)
pro = ts.pro_api()
DSN = "postgresql://quant:quant_pass@localhost:5432/quantdb"
engine = create_engine(DSN)

def get_raw_conn():
    return psycopg2.connect("host=localhost port=5432 dbname=quantdb user=quant password=quant_pass")

def bulk_upsert(table_name, df, pk_cols=None, batch_size=500):
    """Insert DataFrame with ON CONFLICT DO NOTHING"""
    if df is None or df.empty:
        return 0
    
    # Get table columns from DB
    with engine.connect() as conn:
        cols = [row[0] for row in conn.execute(text(
            f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' ORDER BY ordinal_position"
        ))]
    
    # Only use columns that exist in both
    common_cols = [c for c in df.columns if c in cols]
    df_sub = df[common_cols].copy()
    
    if df_sub.empty:
        return 0
    
    inserted = 0
    conn = get_raw_conn()
    cur = conn.cursor()
    
    col_list = ', '.join(common_cols)
    conflict_clause = f" ON CONFLICT ({', '.join(pk_cols)}) DO NOTHING" if pk_cols else ""
    
    for start in range(0, len(df_sub), batch_size):
        batch = df_sub.iloc[start:start+batch_size]
        rows = []
        for _, row in batch.iterrows():
            vals = []
            for c in common_cols:
                v = row[c]
                if pd.isna(v):
                    vals.append(None)
                elif isinstance(v, (pd.Timestamp,)):
                    vals.append(v.strftime('%Y-%m-%d'))
                else:
                    vals.append(v)
            rows.append(tuple(vals))
        
        sql = f"INSERT INTO {table_name} ({col_list}) VALUES %s{conflict_clause}"
        try:
            execute_values(cur, sql, rows, page_size=1000)
            conn.commit()
            inserted += len(rows)
        except Exception as e:
            conn.rollback()
            # Retry one-by-one
            for row in rows:
                try:
                    execute_values(cur, sql, [row], page_size=1000)
                    conn.commit()
                    inserted += 1
                except:
                    conn.rollback()
    
    cur.close()
    conn.close()
    return inserted

def create_table_from_api(table_name, api_name, pk_cols, params=None):
    """Create table matching API fields, or ensure columns exist"""
    fn = getattr(pro, api_name)
    df = fn(**(params or {}))
    if df is None or df.empty:
        print(f"[{api_name}] API returned empty, cannot determine schema")
        return False
    
    # Drop extra metadata columns
    for c in ['id', 'asset_id', 'created_at', 'updated_at']:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)
    
    with engine.connect() as conn:
        existing_cols = set()
        try:
            result = conn.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}'"
            ))
            existing_cols = {row[0] for row in result}
        except:
            pass
        
        if not existing_cols:
            # Create table
            col_defs = []
            for c in df.columns:
                col_type = 'float'
                if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
                    col_type = 'text'
                elif pd.api.types.is_integer_dtype(df[c]):
                    col_type = 'bigint'
                elif pd.api.types.is_datetime64_any_dtype(df[c]):
                    col_type = 'timestamptz'
                col_defs.append(f'"{c}" {col_type}')
            
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
            conn.execute(text(sql))
            if pk_cols:
                try:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD CONSTRAINT uq_{table_name} UNIQUE ({', '.join(pk_cols)})"))
                except:
                    pass
            conn.commit()
            print(f"[{table_name}] CREATED: {len(col_defs)} columns")
        else:
            # Add missing columns
            for c in df.columns:
                if c not in existing_cols:
                    col_type = 'float'
                    if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
                        col_type = 'text'
                    elif pd.api.types.is_integer_dtype(df[c]):
                        col_type = 'bigint'
                    elif pd.api.types.is_datetime64_any_dtype(df[c]):
                        col_type = 'timestamptz'
                    try:
                        conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN "{c}" {col_type}'))
                        conn.commit()
                    except:
                        pass
            print(f"[{table_name}] EXISTS: {len(existing_cols)} columns (+{len(df.columns) - len(existing_cols)} added)")
    return True

# ============================================================
# 1. report_rc — 券商盈利预测
# ============================================================
print("\n" + "="*60)
print("1/4: report_rc — 券商盈利预测")
print("="*60)

create_table_from_api('raw_report_rc', 'report_rc', ['ts_code', 'report_date', 'org_name'], 
                       {'start_date': '20260101', 'end_date': '20260424', 'limit': 5000})

# Pull by quarter from 2010, no pagination (each quarter < 5000 rows)
total_rc = 0
for year in range(2010, 2027):
    for qtr in [(1, '0101', '0331'), (2, '0401', '0630'), (3, '0701', '0930'), (4, '1001', '1231')]:
        q, sd, ed = qtr
        if year == 2026 and q > 2:
            continue
        start = f'{year}{sd}'
        end = f'{year}{ed}'
        
        try:
            df = pro.report_rc(start_date=start, end_date=end, limit=5000)
        except Exception as e:
            print(f"  [{start}-{end}] ERROR: {e}")
            continue
        
        if df is None or df.empty:
            continue
        
        n = bulk_upsert('raw_report_rc', df, ['ts_code', 'report_date', 'org_name'])
        total_rc += n
        if year % 5 == 0:
            print(f"  [{start}] +{n} (total: {total_rc})")
        time.sleep(0.3)

print("[report_rc] DONE")

# ============================================================
# 2. cyq_perf — 每日筹码及胜率
# ============================================================
print("\n" + "="*60)
print("2/4: cyq_perf — 每日筹码及胜率")
print("="*60)

create_table_from_api('raw_cyq_perf', 'cyq_perf', ['ts_code', 'trade_date'],
                       {'ts_code': '000001.SZ', 'start_date': '20260101', 'end_date': '20260424'})

# Get stock list
stocks = pd.read_sql("SELECT ts_code FROM ref_stock_basic WHERE delist_date IS NULL", engine)
stock_codes = stocks['ts_code'].tolist()
print(f"Total stocks: {len(stock_codes)}")

# Pull recent 1 year for all stocks
total = 0
for i, code in enumerate(stock_codes):
    try:
        df = pro.cyq_perf(ts_code=code, start_date='20250101', end_date='20260424')
        n = bulk_upsert('raw_cyq_perf', df, ['ts_code', 'trade_date'])
        total += n
        if (i+1) % 200 == 0:
            print(f"  [{i+1}/{len(stock_codes)}] total inserted: {total}")
    except Exception as e:
        pass
    time.sleep(0.3)

print(f"[cyq_perf] DONE: {total} rows")

# ============================================================
# 3. cyq_chips — 每日筹码分布
# ============================================================
print("\n" + "="*60)
print("3/4: cyq_chips — 每日筹码分布")
print("="*60)

create_table_from_api('raw_cyq_chips', 'cyq_chips', ['ts_code', 'trade_date', 'price'],
                       {'ts_code': '000001.SZ', 'start_date': '20260101', 'end_date': '20260424'})

total = 0
for i, code in enumerate(stock_codes):
    try:
        df = pro.cyq_chips(ts_code=code, start_date='20250101', end_date='20260424')
        n = bulk_upsert('raw_cyq_chips', df, ['ts_code', 'trade_date', 'price'])
        total += n
        if (i+1) % 200 == 0:
            print(f"  [{i+1}/{len(stock_codes)}] total inserted: {total}")
    except:
        pass
    time.sleep(0.3)

print(f"[cyq_chips] DONE: {total} rows")

# ============================================================
# 4. broker_recommend — 券商月度金股
# ============================================================
print("\n" + "="*60)
print("4/4: broker_recommend — 券商月度金股")
print("="*60)

create_table_from_api('raw_broker_recommend', 'broker_recommend', ['month', 'broker', 'ts_code'],
                       {'month': '202604'})

total = 0
for year in range(2010, 2027):
    for month in range(1, 13):
        m = f'{year}{month:02d}'
        if m > '202604':
            break
        try:
            df = pro.broker_recommend(month=m)
            n = bulk_upsert('raw_broker_recommend', df, ['month', 'broker', 'ts_code'])
            total += n
        except:
            pass
        time.sleep(0.3)
    print(f"  [{year}] total: {total}")

print(f"[broker_recommend] DONE: {total} rows")

print("\n" + "="*60)
print("ALL DONE")
print("="*60)
