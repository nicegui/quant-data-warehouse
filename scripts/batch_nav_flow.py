#!/usr/bin/env python3
"""Batch pull for fund_nav + fund_flow (AKShare)."""
import os, sys, time
from datetime import datetime, date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv; load_dotenv(".env")
TOKEN = os.getenv("TUSHARE_TOKEN")
today = date.today().strftime("%Y%m%d")

# ═══════════════════════════════════════
# fund_nav — nav_date iteration  
# ═══════════════════════════════════════
from src.collectors.impl.fund_nav import FundNavCollector
nav = FundNavCollector(TOKEN)
nav_total = 0

start = datetime(2020, 1, 1)
end = datetime.strptime(today, "%Y%m%d")
d = start
day_count = 0

print(f"🔄 fund_nav (daily: {start.strftime('%Y%m%d')} → {today}) ...")

while d <= end:
    if d.weekday() < 5:
        ds = d.strftime("%Y%m%d")
        try:
            raw = nav.fetch(nav_date=ds)
            if raw:
                v = nav.validate(raw)
                w = nav.store_raw(v)
                nav_total += w
            day_count += 1
        except:
            pass
    d += timedelta(days=1)
    time.sleep(0.35)

print(f"  ✅ fund_nav: {nav_total:,d} rows\n")

# ═══════════════════════════════════════
# fund_flow — AKShare, CSI 300 components
# ═══════════════════════════════════════
from src.collectors.impl.fund_flow import FundFlowCollector
from src.collectors.impl.stock_basic import StockBasicCollector

sb = StockBasicCollector(TOKEN)
stocks = sb.fetch()
stock_list = [(r["ts_code"], r["name"]) for r in stocks if r.get("list_status") == "L"]
stock_list.sort(key=lambda x: x[0])
target = stock_list[:300]  # top 300 by code

print(f"🔄 fund_flow ({len(target)} stocks) ...")

ff = FundFlowCollector()
ff_total = 0
for i, (code, name) in enumerate(target, 1):
    mkt = "sh" if code.endswith(".SH") else "sz"
    symbol = code.split(".")[0]
    try:
        raw = ff.fetch(stock=symbol, market=mkt)
        if raw:
            v = ff.validate(raw)
            w = ff.store_raw(v)
            ff_total += w
    except Exception as e:
        pass
    if i % 50 == 0:
        print(f"  [{i}/{len(target)}] {code}: total {ff_total:,d}")
    time.sleep(0.6)

print(f"  ✅ fund_flow: {ff_total:,d} rows\n")

# ═══════════════════════════════════════
print(f"fund_nav:  {nav_total:>12,d}")
print(f"fund_flow: {ff_total:>12,d}")
print(f"TOTAL:     {nav_total+ff_total:>12,d}")
