#!/usr/bin/env python3
"""Batch historical pull V3 — bypasses run() checkpoint injection for date ranges."""
import os, sys, time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv; load_dotenv(".env")
TOKEN = os.getenv("TUSHARE_TOKEN")

START = "20200101"
today = date.today().strftime("%Y%m%d")

# Generate month ranges
d = datetime.strptime(START[:6], "%Y%m")
e = datetime.strptime(today, "%Y%m%d")
months = []
while d <= e:
    m_start = d.strftime("%Y%m") + "01"
    next_m = d + relativedelta(months=1)
    m_end = (next_m - timedelta(days=1)).strftime("%Y%m%d")
    if m_end > today:
        m_end = today
    months.append((m_start, m_end))
    d = next_m

print(f"📅 {len(months)} months ({START} → {today})\n")

# ═══════════════════════════════════════
# RANGE COLLECTORS: fetch → validate → store_raw (no run() to avoid checkpoint injection)
# ═══════════════════════════════════════
from src.collectors.impl.cb_daily import CbDailyCollector
from src.collectors.impl.futures import FuturesCollector
from src.collectors.impl.moneyflow_hsgt import MoneyflowHsgtCollector

range_cols = [
    ("cb_daily", CbDailyCollector(TOKEN)),
    ("fut_daily", FuturesCollector(TOKEN)),
    ("moneyflow_hsgt", MoneyflowHsgtCollector(TOKEN)),
]

totals = {}
for name, col in range_cols:
    total = 0
    print(f"🔄 {name} ...")
    for i, (ms, me) in enumerate(months):
        try:
            raw = col.fetch(start_date=ms, end_date=me)
            if not raw:
                continue
            validated = col.validate(raw)
            written = col.store_raw(validated)
            total += written
            if written or (i+1) % 6 == 0:
                print(f"  {ms[:6]}: +{written:>6,d}  (total: {total:>10,d})")
        except Exception as exc:
            print(f"  {ms[:6]}: ⚠️ {exc}")
        time.sleep(0.4)
    totals[name] = total
    print(f"  ✅ {name}: {total:,d} rows\n")

# ═══════════════════════════════════════
# Fund daily — trade_date only, iterate days
# ═══════════════════════════════════════
from src.collectors.impl.fund import FundCollector

fund_c = FundCollector(TOKEN)
fund_total = 0
print(f"🔄 fund_daily (daily iteration, ~1600 days) ...")

d_start = datetime.strptime(START, "%Y%m%d")
d_end = datetime.strptime(today, "%Y%m%d")
d = d_start
day_count = 0
while d <= d_end:
    if d.weekday() < 5:  # skip weekends
        dt_str = d.strftime("%Y%m%d")
        try:
            raw = fund_c.fetch(trade_date=dt_str)
            if raw:
                validated = fund_c.validate(raw)
                written = fund_c.store_raw(validated)
                fund_total += written
                if written > 0 and (fund_total % 20000 == 0 or day_count % 200 == 0):
                    print(f"  {dt_str}: +{written:,d}  (total: {fund_total:,d})")
            day_count += 1
        except Exception as exc:
            # skip rate-limit errors, continue
            pass
    d += timedelta(days=1)
    time.sleep(0.35)

totals["fund_daily"] = fund_total
print(f"  ✅ fund_daily: {fund_total:,d} rows\n")

# ═══════════════════════════════════════
# summary
# ═══════════════════════════════════════
print("="*60)
print("📊 SUMMARY")
print("="*60)
for n, r in totals.items():
    print(f"  {n:20s}: {r:>12,d}")
print(f"  {'TOTAL':20s}: {sum(totals.values()):>12,d}")
