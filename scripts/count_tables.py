"""Count all tables in the quant database."""
from sqlalchemy import create_engine, text
from src.config.settings import settings

cfg = settings.db
engine = create_engine(f'postgresql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.db}')

with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    ).fetchall()

    total = 0
    for (table,) in rows:
        try:
            cnt = conn.execute(text(f'SELECT count(*) FROM "{table}"')).scalar()
            status = f"{cnt:,} rows" if cnt > 0 else "0 rows (EMPTY)"
            if cnt > 0:
                total += cnt
            print(f"  {table:40s} {status}")
        except Exception as e:
            print(f"  {table:40s} ERROR: {e}")
    print(f"\n  TOTAL: {total:,} rows across all tables")
