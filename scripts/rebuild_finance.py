#!/usr/bin/env python3
"""重建财务4表 — 按季度拉取，psycopg2 ON CONFLICT DO NOTHING"""
import tushare as ts
import pandas as pd
import psycopg2
import psycopg2.extras
import os, sys, time
from datetime import datetime

# ── 配置 ──
DB_DSN = "dbname=quantdb user=quant password=quant_pass host=127.0.0.1 port=5432"

def db_conn():
    return psycopg2.connect(DB_DSN)

def db_exec(sql):
    conn = db_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
    finally:
        conn.close()

def log(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print(f'[{t}] {msg}', flush=True, file=sys.stderr)

# ── Tushare Token ──
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
TOKEN = None
with open(env_path) as f:
    for line in f:
        if line.startswith('TUSHARE_TOKEN='):
            TOKEN = line.split('=', 1)[1].strip()
            break
if not TOKEN:
    log("ERROR: 找不到 TUSHARE_TOKEN")
    sys.exit(1)

pro = ts.pro_api(TOKEN)
log(f"Tushare 已连接 (token: {TOKEN[:8]}...)")

# ── 表定义 ──
# 关键：不指定 fields=，让 API 返回全部字段，psycopg2 自动匹配列
TABLES = {
    'raw_fin_income': {
        'api': 'income_vip',
        'table_cols': [
            'ts_code', 'end_date', 'revenue', 'operate_profit', 'total_revenue',
            'n_income', 'total_profit', 'profit_to_ors', 'minority_interest',
            'basic_eps', 'diluted_eps', 'update_flag', 'f_ann_date',
        ],
    },
    'raw_fin_balance': {
        'api': 'balancesheet_vip',
        'table_cols': [
            'ts_code', 'end_date', 'total_assets', 'total_liab', 'money_cap',
            'goodwill_impair', 'goodwill', 'total_hldr_eqy_inc_min_int',
            'update_flag', 'f_ann_date',
        ],
    },
    'raw_fin_cashflow': {
        'api': 'cashflow_vip',
        'table_cols': [
            'ts_code', 'end_date', 'net_profit', 'free_cashflow',
            'c_fr_sale_sg', 'c_fr_sale_s', 'update_flag',
        ],
    },
    'raw_fin_indicators': {
        'api': 'fina_indicator_vip',
        'table_cols': [
            'ts_code', 'end_date', 'roe', 'roa', 'roe_dt', 'roa_dp',
            'or_yoy', 'eps', 'bps', 'profit_dedt', 'dt_eps', 'update_flag',
        ],
    },
}

# ── 建表 SQL（删旧建新） ──
CREATE_SQL = {
    'raw_fin_income': '''
        CREATE TABLE raw_fin_income (
            ts_code VARCHAR(16), end_date TIMESTAMPTZ,
            revenue DOUBLE PRECISION, operate_profit DOUBLE PRECISION,
            total_revenue DOUBLE PRECISION, n_income DOUBLE PRECISION,
            total_profit DOUBLE PRECISION, profit_to_ors DOUBLE PRECISION,
            minority_interest DOUBLE PRECISION, basic_eps DOUBLE PRECISION,
            diluted_eps DOUBLE PRECISION, update_flag VARCHAR(64),
            f_ann_date TIMESTAMPTZ,
            PRIMARY KEY (ts_code, end_date)
        )
    ''',
    'raw_fin_balance': '''
        CREATE TABLE raw_fin_balance (
            ts_code VARCHAR(16), end_date TIMESTAMPTZ,
            total_assets DOUBLE PRECISION, total_liab DOUBLE PRECISION,
            money_cap DOUBLE PRECISION, goodwill_impair DOUBLE PRECISION,
            goodwill DOUBLE PRECISION, total_hldr_eqy_inc_min_int DOUBLE PRECISION,
            update_flag VARCHAR(64), f_ann_date TIMESTAMPTZ,
            PRIMARY KEY (ts_code, end_date)
        )
    ''',
    'raw_fin_cashflow': '''
        CREATE TABLE raw_fin_cashflow (
            ts_code VARCHAR(16), end_date TIMESTAMPTZ,
            net_profit DOUBLE PRECISION, free_cashflow DOUBLE PRECISION,
            c_fr_sale_sg DOUBLE PRECISION, c_fr_sale_s DOUBLE PRECISION,
            update_flag VARCHAR(64),
            PRIMARY KEY (ts_code, end_date)
        )
    ''',
    'raw_fin_indicators': '''
        CREATE TABLE raw_fin_indicators (
            ts_code VARCHAR(16), end_date TIMESTAMPTZ,
            roe DOUBLE PRECISION, roa DOUBLE PRECISION,
            roe_dt DOUBLE PRECISION, roa_dp DOUBLE PRECISION,
            or_yoy DOUBLE PRECISION, eps DOUBLE PRECISION,
            bps DOUBLE PRECISION, profit_dedt DOUBLE PRECISION,
            dt_eps DOUBLE PRECISION, update_flag VARCHAR(64),
            PRIMARY KEY (ts_code, end_date)
        )
    ''',
}

# ════════════════════════════════════════
# Step 1: 删旧表、建新表
# ════════════════════════════════════════
log('删除旧表（仅旧版混表）...')
db_exec('DROP TABLE IF EXISTS raw_financial_reports CASCADE')
db_exec('DROP TABLE IF EXISTS raw_financial_indicators CASCADE')
log('旧表已清理 ✅')

for name, sql in CREATE_SQL.items():
    db_exec(sql.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS'))
    log(f'建表 {name} ✅（已存在则跳过）')

# ════════════════════════════════════════
# Step 2: 按季度拉取
# ════════════════════════════════════════
q_end = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
# 从2003年开始覆盖茅台等早期股票
quarters = [f'{y}{q_end[q]}' for y in range(2019, 2027) for q in range(1, 5)]

for name, tbl in TABLES.items():
    log(f'\n{"="*50}')
    log(f'开始拉取: {name} ({tbl["api"]})')
    log(f'{"="*50}')
    
    total_inserted = 0
    api_cols = tbl['table_cols']
    
    for end_date in quarters:
        # 调用 API — 不指定 fields，取全部字段后在 Python 里筛选
        df = None
        for retry in range(3):
            try:
                api_fn = getattr(pro, tbl['api'])
                df = api_fn(end_date=end_date)
                time.sleep(0.35)
                break
            except Exception as e:
                if retry < 2:
                    log(f'  {end_date} API重试 {retry+1}/3: {e}')
                    time.sleep(3)
                else:
                    log(f'  {end_date} API最终失败: {e}')
        
        if df is None or df.empty:
            log(f'  {end_date}: 无数据，跳过')
            continue
        
        # 筛选需要的列（API 可能返回超集）
        available_cols = [c for c in api_cols if c in df.columns]
        missing_cols = [c for c in api_cols if c not in df.columns]
        if missing_cols:
            log(f'  {end_date}: API缺列 {missing_cols}，将为NULL')
        
        df_sub = df[available_cols].copy()
        
        # psycopg2 批量 INSERT ... ON CONFLICT DO NOTHING
        conn = db_conn()
        cur = conn.cursor()
        
        # 构建 INSERT SQL — execute_values 用单个 %s 占位
        cols_sql = ', '.join(available_cols)
        sql = f"""
            INSERT INTO {name} ({cols_sql})
            VALUES %s
            ON CONFLICT (ts_code, end_date) DO NOTHING
        """
        template = '(' + ', '.join(['%s'] * len(available_cols)) + ')'
        
        # 转换 DataFrame 为 tuples 列表
        rows = [tuple(row) for row in df_sub.itertuples(index=False)]
        
        try:
            psycopg2.extras.execute_values(cur, sql, rows, template=template, page_size=500)
            conn.commit()
            inserted = cur.rowcount
            total_inserted += inserted
            log(f'  {end_date}: API返回{len(df):,}行, 插入{inserted:,}行 (累计{total_inserted:,})')
        except Exception as e:
            conn.rollback()
            log(f'  {end_date}: INSERT失败: {e}')
            # 降级为逐行插入
            inserted = 0
            for row in rows:
                try:
                    cur.execute(sql, row)
                    inserted += 1
                except Exception:
                    pass
            conn.commit()
            total_inserted += inserted
            log(f'  {end_date}: 降级逐行插入 {inserted:,} 行 (累计{total_inserted:,})')
        finally:
            conn.close()
        
        # 每个季度之间歇一下，避免触发限流
        time.sleep(0.2)
    
    log(f'\n✅ {name} 完成! 总计 {total_inserted:,} 行')

# ════════════════════════════════════════
# Step 3: 最终统计
# ════════════════════════════════════════
log('\n' + '='*50)
log('最终统计')
log('='*50)
conn = db_conn()
cur = conn.cursor()
for name in TABLES:
    cur.execute(f'SELECT COUNT(*) FROM {name}')
    cnt = cur.fetchone()[0]
    cur.execute(f'SELECT COUNT(DISTINCT ts_code) FROM {name}')
    stocks = cur.fetchone()[0]
    log(f'{name:30s}: {cnt:>8,} 行, {stocks:>5} 只股票')
conn.close()
log('\n🎉 全部完成!')
