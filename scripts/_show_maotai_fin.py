"""查茅台4张财务新表的底层数据"""
from sqlalchemy import create_engine, text

DB_URL = "postgresql://quant:quant_pass@localhost:5432/quantdb"
engine = create_engine(DB_URL, pool_pre_ping=True)

with engine.connect() as conn:
    # 1. 表存在性+行数
    print("=" * 60)
    print("📋 财务新表行数")
    print("=" * 60)
    for t in ['raw_fin_income', 'raw_fin_balance', 'raw_fin_cashflow', 'raw_fin_indicators']:
        try:
            r = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
            total = r.scalar()
            r2 = conn.execute(text(f"SELECT COUNT(*) FROM {t} WHERE ts_code='600519.SH'"))
            mt = r2.scalar()
            print(f"  {t}: {total} 行, 茅台={mt} 行")
        except Exception as e:
            print(f"  {t}: ❌ {e}")

    # 2. 茅台数据: raw_fin_income
    print("\n" + "=" * 60)
    print("💰 raw_fin_income — 贵州茅台 (收入/利润)")
    print("=" * 60)
    try:
        r = conn.execute(text("""
            SELECT ts_code, end_date, revenue, total_revenue, operate_profit,
                   total_profit, n_income, basic_eps
            FROM raw_fin_income
            WHERE ts_code = '600519.SH'
            ORDER BY end_date DESC
            LIMIT 12
        """))
        for row in r:
            print(f"  {row[0]} | {str(row[1])[:10]} | "
                  f"营收={row[2]} | 利润总额={row[5]} | 净利润={row[6]} | EPS={row[7]}")
    except Exception as e:
        print(f"  ❌ {e}")

    # 3. raw_fin_balance (取核心列)
    print("\n" + "=" * 60)
    print("🏦 raw_fin_balance — 资产负债表")
    print("=" * 60)
    try:
        r = conn.execute(text("""
            SELECT ts_code, end_date, total_assets, total_liab, total_hldr_eqy_exc_min_int,
                   money_cap, inventories, goodwill
            FROM raw_fin_balance
            WHERE ts_code = '600519.SH'
            ORDER BY end_date DESC
            LIMIT 8
        """))
        for row in r:
            print(f"  {row[0]} | {str(row[1])[:10]} | "
                  f"总资产={row[2]} | 总负债={row[3]} | 净资产={row[4]} | 现金={row[5]}")
    except Exception as e:
        print(f"  ❌ {e}")

    # 4. raw_fin_cashflow
    print("\n" + "=" * 60)
    print("💸 raw_fin_cashflow — 现金流量表")
    print("=" * 60)
    try:
        r = conn.execute(text("""
            SELECT ts_code, end_date, net_profit, free_cashflow,
                   c_fr_sale_sg, c_inf_fr_operate_a
            FROM raw_fin_cashflow
            WHERE ts_code = '600519.SH'
            ORDER BY end_date DESC
            LIMIT 8
        """))
        for row in r:
            print(f"  {row[0]} | {str(row[1])[:10]} | "
                  f"净利润={row[2]} | 自由现金流={row[3]} | 经营现金流={row[5]}")
    except Exception as e:
        print(f"  ❌ {e}")

    # 5. raw_fin_indicators (取核心财务指标)
    print("\n" + "=" * 60)
    print("📊 raw_fin_indicators — 财务指标")
    print("=" * 60)
    try:
        r = conn.execute(text("""
            SELECT ts_code, end_date, roe, roa, grossprofit_margin,
                   netprofit_margin, debt_to_assets, current_ratio
            FROM raw_fin_indicators
            WHERE ts_code = '600519.SH'
            ORDER BY end_date DESC
            LIMIT 12
        """))
        for row in r:
            print(f"  {row[0]} | {str(row[1])[:10]} | "
                  f"ROE={row[2]} | ROA={row[3]} | 毛利率={row[4]} | 净利率={row[5]} | "
                  f"负债率={row[6]} | 流动比={row[7]}")
    except Exception as e:
        print(f"  ❌ {e}")

    print("\n✅ 完成")
