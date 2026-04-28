#!/usr/bin/env python3
"""Pull financial data into existing tables. No drops, no recreates."""
import sys, os, time
import tushare as ts
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
from datetime import date
from dateutil.relativedelta import relativedelta

TOKEN = None
with open(os.path.expanduser("~/quant-data-warehouse/.env")) as f:
    for line in f:
        if line.startswith("TUSHARE_TOKEN="):
            TOKEN = line.split("=", 1)[1].strip()
            break

DB = "postgresql://quant:quant_pass@localhost:5432/quantdb"
ENGINE = sa.create_engine(DB)
pro = ts.pro_api(TOKEN)

TABLES = {
    "raw_fin_income":     ("income_vip",       ["ts_code", "end_date"]),
    "raw_fin_balance":    ("balancesheet_vip", ["ts_code", "end_date"]),
    "raw_fin_cashflow":   ("cashflow_vip",     ["ts_code", "end_date"]),
    "raw_fin_indicators": ("fina_indicator_vip",["ts_code", "end_date"]),
}

QUARTERS = []
d = date(2026, 4, 1)
for _ in range(30):
    QUARTERS.append(d.strftime("%Y%m%d"))
    d = (d - relativedelta(months=3))

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def pull_table(table_name, api_method, pk_cols):
    """Pull all quarters, insert with ON CONFLICT DO NOTHING."""
    log(f"\n=== {table_name} ({api_method}) ===")
    
    # Get existing columns from table
    with ENGINE.connect() as conn:
        existing_cols = pd.read_sql(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_name='{table_name}' AND table_schema='public' ORDER BY ordinal_position",
            conn
        )['column_name'].tolist()
    
    existing_cols = [c for c in existing_cols if c != 'id']  # skip auto id
    
    for i, q in enumerate(QUARTERS):
        start = time.time()
        try:
            fn = getattr(pro, api_method)
            df = fn(end_date=q)

            if df is None or len(df) == 0:
                log(f"  Q{i+1:2d} {q}: 0 rows")
                continue
            
            # Align columns to table schema
            cols = [c for c in existing_cols if c in df.columns]
            df_insert = df[cols].copy()
            
            # Convert to records
            records = df_insert.where(pd.notna(df_insert), None).to_dict(orient='records')
            
            # Build INSERT
            col_list = ", ".join(cols)
            placeholders = ", ".join([f":{c}" for c in cols])
            pk_match = " AND ".join([f"{c} = EXCLUDED.{c}" for c in pk_cols])
            
            # Batch insert
            with ENGINE.begin() as conn:
                conn.execute(text(
                    f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
                    f"ON CONFLICT ({', '.join(pk_cols)}) DO NOTHING"
                ), records)
            
            elapsed = time.time() - start
            log(f"  Q{i+1:2d} {q}: {len(df):,} rows in {elapsed:.1f}s")
            
        except Exception as e:
            elapsed = time.time() - start
            log(f"  Q{i+1:2d} {q}: ERROR after {elapsed:.1f}s - {e}")

# ── MAIN ──
log("=== Financial Data Pull ===")
for table_name, (api_method, pk_cols) in TABLES.items():
    pull_table(table_name, api_method, pk_cols)

log("\n=== Final counts ===")
with ENGINE.connect() as conn:
    for t in TABLES:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        log(f"  {t}: {cnt:,} rows")
