#!/usr/bin/env python3
"""Resume fund_daily from checkpoint + start fund_nav from scratch."""
import os, sys, time
from datetime import datetime, date, timedelta

sys.path.insert(0, '.'); os.chdir('.')
from dotenv import load_dotenv; load_dotenv('.env')
TOKEN = os.getenv('TUSHARE_TOKEN')

from src.collectors.impl.fund import FundCollector
from src.collectors.impl.fund_nav import FundNavCollector

# fund_daily: use run() which auto-resumes from checkpoint
fund = FundCollector(TOKEN)
fund_total = 0
ck = fund.get_checkpoint_date()
print(f"🔄 fund_daily (resume from checkpoint: {ck}) ...\n")

today = date.today()
d = datetime.strptime(ck or "20200101", "%Y%m%d") if ck else datetime(2020,1,1)
end = datetime.strptime(today.strftime("%Y%m%d"), "%Y%m%d")

while d <= end:
    ds = d.strftime("%Y%m%d")
    if d.weekday() < 5:
        try:
            # Bypass checkpoint injection by calling fetch directly
            raw = fund.fetch(trade_date=ds)
            if raw:
                v = fund.validate(raw)
                w = fund.store_raw(v)
                fund_total += w
        except:
            pass
    d += timedelta(days=1)
    time.sleep(0.35)

print(f"  ✅ fund_daily: {fund_total:,d} new rows\n")

# fund_nav
nav = FundNavCollector(TOKEN)
nav_total = 0
print(f"🔄 fund_nav (from 2020-01-01) ...")

d = datetime(2020,1,1)
while d <= end:
    if d.weekday() < 5:
        ds = d.strftime("%Y%m%d")
        try:
            raw = nav.fetch(nav_date=ds)
            if raw:
                v = nav.validate(raw)
                w = nav.store_raw(v)
                nav_total += w
            if nav_total % 200000 == 0:
                print(f"    {ds}: {nav_total:,d}")
        except:
            pass
    d += timedelta(days=1)
    time.sleep(0.35)

print(f"  ✅ fund_nav: {nav_total:,d} rows\n")
print(f"fund_daily: {fund_total:>12,d}")
print(f"fund_nav:   {nav_total:>12,d}")
