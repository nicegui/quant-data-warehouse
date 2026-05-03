#!/usr/bin/env python3
"""Batch pull: 7 fast tables + per-stock financials for top 500 stocks."""
import os, sys, time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)
os.chdir(PROJECT)

from dotenv import load_dotenv; load_dotenv('.env')
TOKEN = os.getenv("TUSHARE_TOKEN")

from src.collectors.impl.stock_basic import StockBasicCollector

# ════════════════════════════════════════════════════════
# Get stock list
# ════════════════════════════════════════════════════════
sb = StockBasicCollector(TOKEN)
stocks = sb.fetch()
stocks.sort(key=lambda x: x['ts_code'])
target = stocks[:500]  # top 500
print(f"📊 {len(target)} stocks for per-stock tables\n")

# ════════════════════════════════════════════════════════
# PHASE 1: Fast tables (date-range capable)
# ════════════════════════════════════════════════════════
from src.collectors.impl.margin import MarginCollector
from src.collectors.impl.sw_daily import SwDailyCollector
from src.collectors.impl.ths_daily import ThsDailyCollector
from src.collectors.impl.index_dailybasic import IndexDailybasicCollector
from src.collectors.impl.cn_ppi import CnPpiCollector
from src.collectors.impl.fund_basic import FundBasicCollector
from src.collectors.impl.repurchase import RepurchaseCollector

FAST_COLS = {
    "margin_total": (MarginCollector(TOKEN), "run"),
    "sw_daily": (SwDailyCollector(TOKEN), "run"),
    "ths_daily": (ThsDailyCollector(TOKEN), "run"),
    "index_dailybasic": (IndexDailybasicCollector(TOKEN), "run"),
    "cn_ppi": (CnPpiCollector(TOKEN), "run"),
    "fund_basic": (FundBasicCollector(TOKEN), "run"),
    "repurchase": (RepurchaseCollector(TOKEN), "run"),
}

start = "20200101"
today = date.today().strftime("%Y%m%d")

# Generate month ranges for date-range tables
d = datetime.strptime(start[:6], "%Y%m")
e = datetime.strptime(today, "%Y%m%d")
month_ranges = []
while d <= e:
    ms = d.strftime("%Y%m") + "01"
    nm = d + relativedelta(months=1)
    me = (nm - timedelta(days=1)).strftime("%Y%m%d")
    if me > today: me = today
    month_ranges.append((ms, me))
    d = nm

print("="*60)
print("PHASE 1: Fast tables (date-range / full-pull)")
print("="*60)

fast_totals = {}
for name, (col, _) in FAST_COLS.items():
    total = 0
    print(f"🔄 {name} ...", flush=True)
    
    if name in ("fund_basic", "repurchase"):
        # Full-pull (no date params)
        try:
            raw = col.fetch()
            if raw:
                v = col.validate(raw)
                total = col.store_raw(v)
        except Exception as exc:
            print(f"  ⚠️ {exc}", flush=True)
    else:
        # Date-range by month
        for i, (ms, me) in enumerate(month_ranges):
            try:
                raw = col.fetch(start_date=ms, end_date=me)
                if raw:
                    v = col.validate(raw)
                    w = col.store_raw(v)
                    total += w
            except Exception:
                pass
            if (i + 1) % 10 == 0:
                print(f"  [{ms[:6]}] {total:,d}", flush=True)
            time.sleep(0.35)
    
    fast_totals[name] = total
    print(f"  ✅ {name}: {total:,d} rows", flush=True)

print(f"\nPhase 1 done: {sum(fast_totals.values()):,d} rows\n")

# ════════════════════════════════════════════════════════
# PHASE 2: Per-stock tables (each stock pulls all history)
# ════════════════════════════════════════════════════════
from src.collectors.impl.financial_reports import FinancialReportCollector
from src.collectors.impl.express import ExpressCollector
from src.collectors.impl.holder_number import StkHolderNumberCollector
from src.collectors.impl.top10_holders import Top10HoldersCollector
from src.collectors.impl.holder import HolderCollector
from src.collectors.impl.block_trade import BlockTradeCollector
from src.collectors.impl.fund_portfolio import FundPortfolioCollector

PER_STOCK_COLS = {
    "balance_sheet": FinancialReportCollector(TOKEN),
    "cash_flow": FinancialReportCollector(TOKEN),
    "fina_indicator": FinancialReportCollector(TOKEN),
    "forecast": FinancialReportCollector(TOKEN),
    "express": ExpressCollector(TOKEN),
    "dividend": FinancialReportCollector(TOKEN),
    "stk_holdernumber": StkHolderNumberCollector(TOKEN),
    "top10_holders": Top10HoldersCollector(TOKEN),
    "stk_holdertrade": HolderCollector(TOKEN),
    "block_trade": BlockTradeCollector(TOKEN),
}

# NOTE: financial_report collector handles multiple sub-tables
# For now, pull the main ones through existing collectors

print("="*60)
print(f"PHASE 2: Per-stock tables ({len(target)} stocks each)")
print("="*60)

# Pull stk_factor, weekly, monthly through their collectors
from src.collectors.impl.stk_factor import StkFactorCollector
from src.collectors.impl.weekly_monthly import WeeklyMonthlyCollector

per_stock_totals = {}

for name, cls, kwargs in [
    ("stk_factor", StkFactorCollector, {}),
    ("weekly", WeeklyMonthlyCollector, {"freq": "W"}),
    ("monthly", WeeklyMonthlyCollector, {"freq": "M"}),
]:
    total = 0
    print(f"🔄 {name} ...", flush=True)
    col = cls(TOKEN, **kwargs) if kwargs else cls(TOKEN)
    for i, row in enumerate(target):
        ts_code = row["ts_code"]
        try:
            raw = col.fetch(ts_code=ts_code, start_date="20200101", end_date=today)
            if raw:
                v = col.validate(raw)
                w = col.store_raw(v)
                total += w
        except:
            pass
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(target)}] {total:,d}", flush=True)
        time.sleep(0.35)
    per_stock_totals[name] = total
    print(f"  ✅ {name}: {total:,d} rows", flush=True)

for name, col in [
    ("stk_holdernumber", StkHolderNumberCollector(TOKEN)),
    ("top10_holders", Top10HoldersCollector(TOKEN)),
]:
    total = 0
    print(f"🔄 {name} ...", flush=True)
    for i, row in enumerate(target):
        ts_code = row["ts_code"]
        try:
            raw = col.fetch(ts_code=ts_code, start_date="20200101", end_date=today)
            if raw:
                v = col.validate(raw)
                w = col.store_raw(v)
                total += w
        except:
            pass
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(target)}] {total:,d}", flush=True)
        time.sleep(0.35)
    per_stock_totals[name] = total
    print(f"  ✅ {name}: {total:,d} rows", flush=True)

# ════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════
print("\n" + "="*60)
print("📊 BATCH SUMMARY")
print("="*60)
for name, n in {**fast_totals, **per_stock_totals}.items():
    print(f"  {name:25s}: {n:>10,d}")
print(f"  {'TOTAL':25s}: {sum(fast_totals.values()) + sum(per_stock_totals.values()):>10,d}")
