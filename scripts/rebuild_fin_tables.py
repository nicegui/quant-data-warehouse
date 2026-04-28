#!/usr/bin/env python3
"""Drop and recreate 4 financial tables with correct schema from API fields."""
import os, sys, tushare as ts
from sqlalchemy import create_engine, text

# Read token
with open(os.path.expanduser("~/quant-data-warehouse/.env")) as f:
    for line in f:
        line = line.strip()
        if "TUSHARE_TOKEN" in line:
            token = line.split("=", 1)[1].strip().strip("'\"")
            break

pro = ts.pro_api(token)
engine = create_engine("postgresql://quant:quant_pass@localhost:5432/quantdb", pool_pre_ping=True)

tables = [
    ("raw_fin_income", "income_vip"),
    ("raw_fin_balance", "balancesheet_vip"),
    ("raw_fin_cashflow", "cashflow_vip"),
    ("raw_fin_indicators", "fina_indicator_vip"),
]

for table_name, api_name in tables:
    # Get columns from API
    api_func = getattr(pro, api_name)
    df = api_func(ts_code="000001.SZ", start_date="20231231", end_date="20241231", limit=1)
    fields = list(df.columns)
    print(f"[{table_name}] {len(fields)} columns from API")

    col_defs = ['"id" BIGSERIAL PRIMARY KEY']
    for col in fields:
        cl = col.lower()
        if cl in ("ts_code", "end_date", "ann_date", "f_ann_date", "report_type", "comp_type", "end_type", "update_flag"):
            col_defs.append(f'"{col}" VARCHAR(32)')
        elif "date" in cl or "month" in cl or "quarter" in cl:
            col_defs.append(f'"{col}" VARCHAR(16)')
        else:
            col_defs.append(f'"{col}" DOUBLE PRECISION')

    create_sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})'
    uq_sql = f'ALTER TABLE "{table_name}" ADD CONSTRAINT "uq_{table_name}" UNIQUE ("ts_code", "end_date")'

    # Execute in separate transactions to avoid cascading rollback
    create_if_not_exists = create_sql.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS')
    with engine.begin() as conn:
        conn.execute(text(create_if_not_exists))
    print(f"  Ensured exists ✓")

    with engine.begin() as conn:
        conn.execute(text(uq_sql))
    print(f"  Unique constraint added ✓")

    # Verify
    with engine.connect() as conn:
        cnt = conn.execute(text(f"SELECT count(*) FROM information_schema.columns WHERE table_name = '{table_name}'")).scalar()
        row_cnt = conn.execute(text(f"SELECT count(*) FROM \"{table_name}\"")).scalar()
        print(f"  Verified: {cnt} columns, {row_cnt} rows ✓")
    print()
