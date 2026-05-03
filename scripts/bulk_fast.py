#!/usr/bin/env python3
"""Fast bulk insert for stk_factor, stock_weekly, stock_monthly using UPSERT."""
import os, sys, time
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT); os.chdir(PROJECT)
from dotenv import load_dotenv; load_dotenv('.env')
import tushare as ts
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import inspect
from src.db.session import db_session
from src.models.market import RawStkFactor, RawStockWeekly, RawStockMonthly
from src.models.fund import RawFundPortfolio

pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))
today = "20260501"

# Get stocks
stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code')
codes = [r['ts_code'] for r in stocks.to_dict('records')][:500]
print(f"Target: {len(codes)} stocks")

def bulk_upsert(table_name, columns, records, conflict_cols):
    """Fast bulk insert with ON CONFLICT DO NOTHING."""
    if not records:
        return 0
    conn = psycopg2.connect("host=127.0.0.1 dbname=quantdb")
    cur = conn.cursor()
    col_names = [c for c in columns if c not in ('id', 'created_at', 'updated_at')]
    # Filter records to only include valid columns
    clean = [{k: v for k, v in r.items() if k in col_names} for r in records]
    # Build SQL
    placeholders = ', '.join(['%s'] * len(col_names))
    quoted_cols = ', '.join(f'"{c}"' for c in col_names)
    conflict = ', '.join(f'"{c}"' for c in conflict_cols)
    sql = f'INSERT INTO {table_name} ({quoted_cols}) VALUES %s ON CONFLICT ({conflict}) DO NOTHING'
    values = [[r.get(c) for c in col_names] for r in clean]
    execute_values(cur, sql, values, page_size=1000)
    written = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return written

def get_model_columns(model):
    return [c.name for c in model.__table__.columns]

# === stk_factor ===
print("\n=== STK_FACTOR ===")
cols = get_model_columns(RawStkFactor)
total = 0
for i, code in enumerate(codes):
    try:
        df = pro.stk_factor(ts_code=code, start_date="20200101", end_date=today)
        if df is not None and not df.empty:
            w = bulk_upsert('raw_stk_factor', cols, df.to_dict('records'), ['ts_code', 'trade_date'])
            total += w
    except: pass
    if (i+1) % 50 == 0:
        print(f"  [{i+1}/{len(codes)}] {total:,}", flush=True)
    time.sleep(0.35)
print(f"✅ stk_factor: {total:,}", flush=True)

# === stock_weekly ===
print("\n=== STOCK_WEEKLY ===")
cols = get_model_columns(RawStockWeekly)
total = sum(1 for _ in [])  # reset
total = 0
for i, code in enumerate(codes):
    try:
        df = pro.weekly(ts_code=code, start_date="20200101", end_date=today)
        if df is not None and not df.empty:
            w = bulk_upsert('raw_stock_weekly', cols, df.to_dict('records'), ['ts_code', 'trade_date'])
            total += w
    except: pass
    if (i+1) % 50 == 0:
        print(f"  [{i+1}/{len(codes)}] {total:,}", flush=True)
    time.sleep(0.35)
print(f"✅ stock_weekly: {total:,}", flush=True)

# === stock_monthly ===
print("\n=== STOCK_MONTHLY ===")
cols = get_model_columns(RawStockMonthly)
total = 0
for i, code in enumerate(codes):
    try:
        df = pro.monthly(ts_code=code, start_date="20200101", end_date=today)
        if df is not None and not df.empty:
            w = bulk_upsert('raw_stock_monthly', cols, df.to_dict('records'), ['ts_code', 'trade_date'])
            total += w
    except: pass
    if (i+1) % 50 == 0:
        print(f"  [{i+1}/{len(codes)}] {total:,}", flush=True)
    time.sleep(0.35)
print(f"✅ stock_monthly: {total:,}", flush=True)

# === fund_portfolio ===
print("\n=== FUND_PORTFOLIO ===")
cols = get_model_columns(RawFundPortfolio)
total = 0
for i, code in enumerate(codes[:100]):  # Only 100 funds
    fund_code = code.replace(".SH", ".OF").replace(".SZ", ".OF")
    try:
        df = pro.fund_portfolio(ts_code=fund_code)
        if df is not None and not df.empty:
            w = bulk_upsert('raw_fund_portfolio', cols, df.to_dict('records'), ['ts_code', 'end_date', 'symbol'])
            total += w
    except: pass
    if (i+1) % 20 == 0:
        print(f"  [{i+1}/100] {total:,}", flush=True)
    time.sleep(0.35)
print(f"✅ fund_portfolio: {total:,}", flush=True)

print("\n🎉 ALL DONE")
