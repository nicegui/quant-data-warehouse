#!/usr/bin/env python3
"""fund_daily standalone — high-frequency progress logging."""
import os, sys, time
from datetime import datetime, date, timedelta
sys.path.insert(0, '.'); os.chdir('.')
from dotenv import load_dotenv; load_dotenv('.env')
from src.collectors.impl.fund import FundCollector

c = FundCollector(os.getenv('TUSHARE_TOKEN'))
total = 0
days = 0

d = datetime(2020, 1, 1)
end = datetime.strptime(date.today().strftime("%Y%m%d"), "%Y%m%d")

print(f"🔄 fund_daily ({d.strftime('%Y%m%d')} → {end.strftime('%Y%m%d')})")
print(f"   进度每 100 天汇报一次\n")

while d <= end:
    if d.weekday() < 5:
        ds = d.strftime("%Y%m%d")
        try:
            raw = c.fetch(trade_date=ds)
            if raw:
                v = c.validate(raw)
                w = c.store_raw(v)
                total += w
            days += 1
        except:
            pass
        if days % 100 == 0:
            print(f"  [{days}] {ds}: {total:,d} rows")
    d += timedelta(days=1)
    time.sleep(0.35)

print(f"\n✅ fund_daily: {total:,d} rows ({days} trading days)")
