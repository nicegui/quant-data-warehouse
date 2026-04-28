#!/usr/bin/env python3
"""贵州茅台 (600519.SH) 年线 + 财务指标叠加图"""
import os, sys
sys.path.insert(0, '/Users/admin/quant-data-warehouse')
from dotenv import load_dotenv
load_dotenv('/Users/admin/quant-data-warehouse/.env')

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine

DB_URL = os.getenv('DB_URL', 'postgresql://quant:***@localhost:5432/quantdb')
# Unmask the password
DB_URL = DB_URL.replace('***', os.getenv('POSTGRES_PASSWORD', 'quant_pass'))
engine = create_engine(DB_URL)

# ===== 1. 年K线 =====
daily = pd.read_sql("""
    SELECT trade_date, open, high, low, close, vol, amount
    FROM raw_stock_daily
    WHERE ts_code = '600519.SH'
    ORDER BY trade_date
""", engine, parse_dates=['trade_date'])

daily.set_index('trade_date', inplace=True)
yearly = daily.resample('YE').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
    'vol': 'sum', 'amount': 'sum'
})
yearly.index = yearly.index.year

# ===== 2. 财务数据 =====
income = pd.read_sql("""
    SELECT end_date, revenue, n_income_attr_p
    FROM raw_fin_income
    WHERE ts_code = '600519.SH'
    ORDER BY end_date
""", engine, parse_dates=['end_date'])
income['year'] = income['end_date'].dt.year.astype(int)
income_yearly = income.groupby('year').last().reset_index()

indicators = pd.read_sql("""
    SELECT end_date, roe, roa, eps
    FROM raw_fin_indicators
    WHERE ts_code = '600519.SH'
    ORDER BY end_date
""", engine, parse_dates=['end_date'])
indicators['year'] = indicators['end_date'].dt.year.astype(int)
ind_yearly = indicators.groupby('year').last().reset_index()

# ===== 3. PE/PB =====
daily_basic = pd.read_sql("""
    SELECT trade_date, pe, pb
    FROM raw_daily_basic
    WHERE ts_code = '600519.SH'
    ORDER BY trade_date
""", engine, parse_dates=['trade_date'])
daily_basic.set_index('trade_date', inplace=True)
pe_pb = daily_basic.resample('YE').last()
pe_pb.index = pe_pb.index.year.astype(int)

# ===== 4. 合并财务数据 =====
fin = income_yearly.merge(ind_yearly, on='year', how='left')

# ===== 5. 图表 =====
fig = plt.figure(figsize=(20, 28))
fig.patch.set_facecolor('#0f172a')

c = {
    'bg': '#0f172a', 'grid': '#1e293b',
    'up': '#ef4444', 'down': '#22c55e',
    'text': '#e2e8f0', 'muted': '#64748b',
    'revenue': '#3b82f6', 'profit': '#f59e0b',
    'roe': '#22c55e', 'eps': '#a78bfa',
    'pe': '#f59e0b', 'roa': '#06b6d4',
}

# 图1: 年K线
ax1 = plt.subplot(6, 1, 1)
ax1.set_facecolor(c['bg'])
for idx, row in yearly.iterrows():
    clr = c['up'] if row['close'] >= row['open'] else c['down']
    ax1.plot([idx, idx], [row['low'], row['high']], color=clr, linewidth=0.8, alpha=0.6)
    ax1.bar(idx, abs(row['close'] - row['open']),
            bottom=min(row['open'], row['close']),
            width=0.5, color=clr, alpha=0.9)
for y in [2005, 2007, 2010, 2012, 2015, 2017, 2020, 2021, 2025]:
    if y in yearly.index:
        ax1.annotate(f'{yearly.loc[y, "close"]:.0f}', (y, yearly.loc[y, 'close']),
                    textcoords='offset points', xytext=(0, 8), fontsize=7,
                    color=c['text'], ha='center', alpha=0.7)
ax1.set_yscale('log')
ax1.set_title('贵州茅台 (600519.SH) — 年K线 (对数坐标)', color=c['text'], fontsize=14, fontweight='bold', pad=15)
ax1.set_ylabel('价格 (元)', color=c['muted'], fontsize=10)
ax1.tick_params(colors=c['muted'], labelsize=8)
ax1.grid(True, alpha=0.15, color=c['grid'])
for s in ax1.spines.values():
    s.set_color(c['grid'])

# 图2: 营收 & 净利润
ax2 = plt.subplot(6, 1, 2)
ax2.set_facecolor(c['bg'])
ax2.bar(fin['year'], fin['revenue']/1e8, color=c['revenue'], alpha=0.7, label='营收 (亿元)', width=0.6)
ax2.bar(fin['year'], fin['n_income_attr_p']/1e8, color=c['profit'], alpha=0.8, label='净利润 (亿元)', width=0.6)
ax2.set_title('营收 & 净利润', color=c['text'], fontsize=12, fontweight='bold', pad=10)
ax2.set_ylabel('亿元', color=c['muted'], fontsize=10)
ax2.legend(loc='upper left', fontsize=8, facecolor=c['bg'], labelcolor=c['text'])
ax2.tick_params(colors=c['muted'], labelsize=8)
ax2.grid(True, alpha=0.15, color=c['grid'])
for s in ax2.spines.values():
    s.set_color(c['grid'])
ax2.set_xlim(fin['year'].min()-0.5, fin['year'].max()+0.5)

# 图3: ROE
ax3 = plt.subplot(6, 1, 3)
ax3.set_facecolor(c['bg'])
ax3.plot(ind_yearly['year'], ind_yearly['roe'], color=c['roe'], linewidth=2, marker='o', markersize=5, label='ROE (%)')
ax3.axhline(20, color=c['profit'], ls='--', alpha=0.4, lw=0.8)
ax3.axhline(30, color=c['up'], ls='--', alpha=0.4, lw=0.8)
ax3.fill_between(ind_yearly['year'], ind_yearly['roe'], 0, alpha=0.1, color=c['roe'])
ax3.set_title('ROE (%)', color=c['text'], fontsize=12, fontweight='bold', pad=10)
ax3.set_ylabel('ROE %', color=c['muted'], fontsize=10)
ax3.legend(loc='upper left', fontsize=8, facecolor=c['bg'], labelcolor=c['text'])
ax3.tick_params(colors=c['muted'], labelsize=8)
ax3.grid(True, alpha=0.15, color=c['grid'])
for s in ax3.spines.values():
    s.set_color(c['grid'])
ax3.set_xlim(ind_yearly['year'].min()-0.5, ind_yearly['year'].max()+0.5)

# 图4: EPS
ax4 = plt.subplot(6, 1, 4)
ax4.set_facecolor(c['bg'])
ax4.bar(ind_yearly['year'], ind_yearly['eps'], color=c['eps'], alpha=0.7, width=0.6)
ax4.set_title('EPS (每股收益)', color=c['text'], fontsize=12, fontweight='bold', pad=10)
ax4.set_ylabel('EPS (元)', color=c['muted'], fontsize=10)
ax4.tick_params(colors=c['muted'], labelsize=8)
ax4.grid(True, alpha=0.15, color=c['grid'])
for s in ax4.spines.values():
    s.set_color(c['grid'])
ax4.set_xlim(ind_yearly['year'].min()-0.5, ind_yearly['year'].max()+0.5)

# 图5: PE
ax5 = plt.subplot(6, 1, 5)
ax5.set_facecolor(c['bg'])
ax5.fill_between(pe_pb.index, pe_pb['pe'], 0, alpha=0.3, color=c['pe'])
ax5.plot(pe_pb.index, pe_pb['pe'], color=c['pe'], linewidth=2, marker='o', markersize=4)
ax5.axhline(20, color=c['roe'], ls='--', alpha=0.4, lw=0.8)
ax5.axhline(50, color=c['up'], ls='--', alpha=0.4, lw=0.8)
ax5.set_title('市盈率 PE (年末)', color=c['text'], fontsize=12, fontweight='bold', pad=10)
ax5.set_ylabel('PE', color=c['muted'], fontsize=10)
ax5.tick_params(colors=c['muted'], labelsize=8)
ax5.grid(True, alpha=0.15, color=c['grid'])
for s in ax5.spines.values():
    s.set_color(c['grid'])

# 图6: ROA
ax6 = plt.subplot(6, 1, 6)
ax6.set_facecolor(c['bg'])
ax6.bar(ind_yearly['year'], ind_yearly['roa'], color=c['roa'], alpha=0.7, width=0.6)
ax6.set_title('ROA (总资产收益率 %)', color=c['text'], fontsize=12, fontweight='bold', pad=10)
ax6.set_ylabel('ROA %', color=c['muted'], fontsize=10)
ax6.set_xlabel('年份', color=c['muted'], fontsize=10)
ax6.tick_params(colors=c['muted'], labelsize=8)
ax6.grid(True, alpha=0.15, color=c['grid'])
for s in ax6.spines.values():
    s.set_color(c['grid'])
ax6.set_xlim(ind_yearly['year'].min()-0.5, ind_yearly['year'].max()+0.5)

plt.tight_layout(pad=3.0)
os.makedirs('/Users/admin/quant-data-warehouse/output', exist_ok=True)
plt.savefig('/Users/admin/quant-data-warehouse/output/maotai_fundamental.png',
            dpi=160, bbox_inches='tight', facecolor=c['bg'])
plt.close()
print("DONE")
print(f"数据统计:")
print(f"  年K线: {len(yearly)} 年 ({yearly.index.min()}-{yearly.index.max()})")
print(f"  财务数据: {len(income_yearly)} 年财报 ({fin['year'].min()}-{fin['year'].max()})")
print(f"  PE/PB: {len(pe_pb)} 年")
