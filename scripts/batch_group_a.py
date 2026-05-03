#!/usr/bin/env python3
"""Group A: date-range capable collectors — monthly batch pull."""
import os, sys, time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv; load_dotenv(".env")
TOKEN = os.getenv("TUSHARE_TOKEN")

from src.collectors.impl.cb_daily import CbDailyCollector
from src.collectors.impl.futures import FuturesCollector
from src.collectors.impl.moneyflow_hsgt import MoneyflowHsgtCollector

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

print(f"📅 {len(months)} months ({START} → {today})")
print()

collectors = [
    ("cb_daily", CbDailyCollector(TOKEN)),
    ("fut_daily", FuturesCollector(TOKEN)),
    ("moneyflow_hsgt", MoneyflowHsgtCollector(TOKEN)),
]

totals = {}
for name, col in collectors:
    total = 0
    print(f"🔄 {name} ...")
    for i, (ms, me) in enumerate(months):
        try:
            res = col.run(start_date=ms, end_date=me)
            w = res.get("written", 0)
            total += w
            if w or (i+1) % 6 == 0:
                print(f"  {ms[:6]}: +{w:>5d}  (total: {total:>8,d})")
        except Exception as e:
            print(f"  {ms[:6]}: ⚠️ {e}")
        time.sleep(0.4)
    totals[name] = total
    print(f"  ✅ {name}: {total:,d} rows\n")

print("="*50)
print("Group A Summary:")
for n, r in totals.items():
    print(f"  {n:20s}: {r:>10,d}")
print(f"  {'TOTAL':20s}: {sum(totals.values()):>10,d}")
