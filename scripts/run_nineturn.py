import os, sys, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', stream=sys.stdout)
sys.stdout.reconfigure(line_buffering=True)

from dotenv import load_dotenv; load_dotenv('.env')
from src.collectors.impl.stk_nineturn import StkNineturnCollector
from src.db.session import db_session
from sqlalchemy import text

c = StkNineturnCollector(os.getenv('TUSHARE_TOKEN'), workers=6)
r = c.run()
print(f'stk_nineturn => {r}', flush=True)

with db_session() as s:
    cnt = s.execute(text('SELECT count(*) FROM raw_stk_nineturn')).scalar()
    stocks = s.execute(text('SELECT count(DISTINCT ts_code) FROM raw_stk_nineturn')).scalar()
    print(f'DB: {cnt:,} rows / {stocks} stocks', flush=True)
