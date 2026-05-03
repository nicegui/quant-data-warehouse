#!/usr/bin/env python3
"""Resume fund_daily from 2022-02-24 → today, then fund_nav from 2020."""
import os, sys, time
from datetime import datetime, date, timedelta

PROJECT = '/Users/lawrence/.openclaw/workspace/quant-data-warehouse'
sys.path.insert(0, PROJECT); os.chdir(PROJECT)

from dotenv import load_dotenv; load_dotenv('.env')
TOKEN = os.getenv('TUSHARE_TOKEN')
from src.collectors.impl.fund import FundCollector
from src.collectors.impl.fund_nav import FundNavCollector

today = date.today()
END = datetime.strptime(today.strftime("%Y%m%d"), "%Y%m%d")

# ── fund_daily: resume from last known date in DB ──
from src.db.session import db_session
from src.models.fund import RawFundDaily
with db_session() as s:
    last = s.query(RawFundDaily.trade_date).order_by(RawFundDaily.trade_date.desc()).first()

START_DAYS = last[0] if last else "20200101"
if isinstance(START_DAYS, datetime):
    START_DAYS = START_DAYS.strftime("%Y%m%d")

d = datetime.strptime(START_DAYS, "%Y%m%d") + timedelta(days=1)
print(f"🔄 fund_daily 续传: {d.strftime('%Y%m%d')} → {today}", flush=True)

fund = FundCollector(TOKEN)
fund_total = 0
days = 0
while d <= END:
    ds = d.strftime("%Y%m%d")
    if d.weekday() < 5:
        try:
            raw = fund.fetch(trade_date=ds)
            if raw:
                v = fund.validate(raw)
                w = fund.store_raw(v)
                fund_total += w
                days += 1
        except Exception as e:
            pass
        if days % 50 == 0 or (fund_total > 0 and fund_total % 50000 == 0):
            print(f"  {ds}: {fund_total:>10,d} rows (new)", flush=True)
    d += timedelta(days=1)
    time.sleep(0.35)

print(f"  ✅ fund_daily: +{fund_total:,d} new rows\n", flush=True)

# ── fund_nav: from scratch ──
print(f"🔄 fund_nav: 20200101 → {today}", flush=True)

nav = FundNavCollector(TOKEN)
nav_total = 0
nav_days = 0
d = datetime(2020, 1, 1)
while d <= END:
    ds = d.strftime("%Y%m%d")
    if d.weekday() < 5:
        try:
            raw = nav.fetch(nav_date=ds)
            if raw:
                v = nav.validate(raw)
                w = nav.store_raw(v)
                nav_total += w
                nav_days += 1
        except:
            pass
        if nav_days % 50 == 0:
            print(f"  {ds}: {nav_total:>12,d} rows", flush=True)
    d += timedelta(days=1)
    time.sleep(0.35)

print(f"  ✅ fund_nav: {nav_total:,d} rows\n", flush=True)
print(f"fund_daily new: {fund_total:>12,d}")
print(f"fund_nav total: {nav_total:>12,d}")
