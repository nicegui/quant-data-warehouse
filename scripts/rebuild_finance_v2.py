#!/usr/bin/env python3
"""Rebuild 4 financial tables with columns exactly matching Tushare API response."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tushare as ts
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
from datetime import date
from dateutil.relativedelta import relativedelta

# ── Config ──
TOKEN = None
with open(os.path.expanduser("~/quant-data-warehouse/.env")) as f:
    for line in f:
        if line.startswith("TUSHARE_TOKEN="):
            TOKEN = line.split("=", 1)[1].strip()
            break

DB = "postgresql://quant:quant_pass@localhost:5432/quantdb"
ENGINE = sa.create_engine(DB)

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

pro = ts.pro_api(TOKEN)

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_table_columns(api_method):
    """Get real column names from a single API call."""
    fn = getattr(pro, api_method)
    df = fn(end_date="20260101", limit=1)
    return list(df.columns)

def ensure_table(name, columns):
    """Create table if not exists; add missing columns if exists."""
    # Check if table exists
    with ENGINE.begin() as conn:
        exists = conn.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{name}')"
        )).scalar()

    if not exists:
        col_defs = []
        for col in columns:
            if col in ("ts_code", "ann_date", "f_ann_date", "end_date", "report_type",
                        "comp_type", "end_type", "update_flag"):
                col_defs.append(f"{col} VARCHAR")
            else:
                col_defs.append(f"{col} DOUBLE PRECISION")
        col_ddl = ",\n    ".join(col_defs)
        ddl = f"CREATE TABLE {name} (\n    id BIGSERIAL PRIMARY KEY,\n    {col_ddl}\n)"
        with ENGINE.begin() as conn:
            conn.execute(text(ddl))
        log(f"  {name}: CREATED ({len(columns)} cols)")
    else:
        # Add any missing columns
        existing = get_existing_cols(name)
        for col in columns:
            if col not in existing and col != 'id':
                dtype = 'VARCHAR' if col in ("ts_code", "ann_date", "f_ann_date",
                    "end_date", "report_type", "comp_type", "end_type", "update_flag") else 'DOUBLE PRECISION'
                with ENGINE.begin() as conn:
                    conn.execute(text(f'ALTER TABLE {name} ADD COLUMN {col} {dtype}'))
                log(f"  {name}: +col {col}")
        log(f"  {name}: EXISTS ({len(existing)} cols), checked {len(columns)} API cols")

def get_existing_cols(name):
    with ENGINE.connect() as conn:
        cols = conn.execute(text(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{name}'"
        )).fetchall()
    return {c[0] for c in cols}
    log(f"  Created {name} ({len(columns)} columns)")

def add_unique_constraint(name, pk_cols):
    col_list = ", ".join(pk_cols)
    with ENGINE.begin() as conn:
        # Clean duplicates first
        conn.execute(text(f"""
            DELETE FROM {name} WHERE id NOT IN (
                SELECT MIN(id) FROM {name} GROUP BY {col_list}
            )
        """))
        try:
            conn.execute(text(f"""
                ALTER TABLE {name} ADD CONSTRAINT {name}_uq 
                UNIQUE ({col_list})
            """))
        except Exception:
            pass  # already exists

def pull_table(table_name, api_method, pk_cols):
    """Pull all quarters of data."""
    log(f"=== Pulling {table_name} via {api_method} ===")
    
    for i, q in enumerate(QUARTERS):
        log(f"  Quarter {i+1}/{len(QUARTERS)}: {q}")
        
        try:
            fn = getattr(pro, api_method)
            df = fn(end_date=q)
            
            if df is None or len(df) == 0:
                log(f"    → 0 rows, skip")
                continue
            
            log(f"    → API returned {len(df)} rows")
            
            # Drop columns not in table schema
            with ENGINE.connect() as conn:
                existing_cols = pd.read_sql(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name='{table_name}' AND table_schema='public'",
                    conn
                )['column_name'].tolist()
            
            # Keep only columns that exist in table (exclude id, which is auto)
            cols_to_insert = [c for c in df.columns if c in existing_cols]
            df = df[cols_to_insert]
            
            # Build INSERT ON CONFLICT DO NOTHING
            col_list = ", ".join(cols_to_insert)
            placeholders = ", ".join([f":{c}" for c in cols_to_insert])
            pk_match = " AND ".join([f"{c} = EXCLUDED.{c}" for c in pk_cols])
            
            sql = f"""
                INSERT INTO {table_name} ({col_list})
                VALUES ({placeholders})
                ON CONFLICT ({', '.join(pk_cols)})
                DO NOTHING
            """
            
            with ENGINE.begin() as conn:
                records = df.to_dict(orient='records')
                conn.execute(text(sql), records)
            
            log(f"    → Inserted")
            
        except Exception as e:
            log(f"    ✗ ERROR: {e}")
            continue

# ── MAIN ──
log("=== Phase 1: Get real columns from API ===")
for table_name, (api_method, pk_cols) in TABLES.items():
    columns = get_table_columns(api_method)
    TABLES[table_name] = (api_method, pk_cols, columns)
    log(f"  {api_method}: {len(columns)} fields")

log("\n=== Phase 2: Drop and recreate tables ===")
for table_name, (api_method, pk_cols, columns) in TABLES.items():
    drop_table(table_name)
    create_table(table_name, columns)
    add_unique_constraint(table_name, pk_cols)

log("\n=== Phase 3: Pull data ===")
for table_name, (api_method, pk_cols, columns) in TABLES.items():
    pull_table(table_name, api_method, pk_cols)

log("\n=== Done! Final counts ===")
with ENGINE.connect() as conn:
    for table_name in TABLES:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        log(f"  {table_name}: {cnt:,} rows")
