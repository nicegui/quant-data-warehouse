import sys
sys.path.insert(0, '/Users/admin/quant-data-warehouse/scripts')
from common import get_engine
engine = get_engine()

with engine.connect() as conn:
    # 查所有fin表
    rows = conn.execute(conn.text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%fin%' ORDER BY table_name"))
    print("存在的fin表:", [r[0] for r in rows])

    for t in ['raw_fin_income', 'raw_fin_balance', 'raw_fin_cashflow', 'raw_fin_indicators']:
        r = conn.execute(conn.text(f"SELECT COUNT(*) FROM {t}"))
        cnt = r.scalar()
        r2 = conn.execute(conn.text(f"SELECT COUNT(*) FROM {t} WHERE ts_code='600519.SH'"))
        mt_cnt = r2.scalar()
        print(f"{t}: {cnt} 行, 茅台: {mt_cnt} 行")
