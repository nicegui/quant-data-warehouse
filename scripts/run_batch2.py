"""Run all remaining collectors sequentially: stk_factor_pro → ccass_hold_detail → hk_hold"""
import os, sys, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', stream=sys.stdout)
sys.stdout.reconfigure(line_buffering=True)

from dotenv import load_dotenv; load_dotenv('.env')
token = os.getenv('TUSHARE_TOKEN')

from src.db.session import db_session
from sqlalchemy import text

# ── 1. stk_factor_pro ──
from src.collectors.impl.stk_factor_pro import StkFactorProCollector
print('=== 1/3 stk_factor_pro ===', flush=True)
c1 = StkFactorProCollector(token, workers=8)
r1 = c1.run()
print(f'stk_factor_pro => {r1}', flush=True)

# ── 2. ccass_hold_detail ──
from src.collectors.impl.ccass_hold_detail import CcassHoldDetailCollector
print('=== 2/3 ccass_hold_detail ===', flush=True)
c2 = CcassHoldDetailCollector(token, workers=5)
r2 = c2.run()
print(f'ccass_hold_detail => {r2}', flush=True)

# ── 3. hk_hold ──
from src.collectors.impl.hk_hold import HkHoldCollector
print('=== 3/3 hk_hold ===', flush=True)
c3 = HkHoldCollector(token, workers=6)
r3 = c3.run()
print(f'hk_hold => {r3}', flush=True)

# ── Summary ──
with db_session() as s:
    for t in ['raw_stk_factor_pro', 'raw_ccass_hold_detail', 'raw_hk_hold']:
        cnt = s.execute(text(f'SELECT count(*) FROM {t}')).scalar()
        stocks = s.execute(text(f'SELECT count(DISTINCT ts_code) FROM {t}')).scalar()
        print(f'{t}: {cnt:,} / {stocks} stocks', flush=True)
print('=== ALL DONE ===', flush=True)
