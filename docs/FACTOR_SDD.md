# 因子库 SDD (Software Design Document)

## 1. 概述

### 1.1 目标
从 quant-data-warehouse 的 ~180 张 raw 表中，提取标准化初级因子，供回测引擎消费。

### 1.2 设计原则
- 每个因子 = 一个独立可复现函数，输入 raw 表 + 参数，输出 DataFrame (date × stock, 单列)
- 单因子数据结构：`pd.DataFrame`，index=date，columns=ts_code，values=因子值
- 因子分为 8 大类，每类一个模块文件
- 因子计算纯向量化（pandas/numpy），不依赖回测框架

---

## 2. 数据资产盘点

### 2.1 核心行情层 (>1000 万行)
| 表 | 行数 | 内容 |
|----|------|------|
| raw_stock_daily | 423万 | A股日线 OHLCV |
| raw_index_daily | 1387万 | 指数日线 |
| raw_sw_daily | 74万 | 申万行业日线 |
| raw_dc_daily | 147万 | 东方财富概念板块日线 |
| raw_stock_weekly | 16万 | 周线 |
| raw_stock_monthly | 3.8万 | 月线 |

### 2.2 资金/情绪层
| 表 | 行数 | 内容 |
|----|------|------|
| raw_moneyflow | 304万 | Tushare 个股资金流 |
| raw_moneyflow_dc | 513万 | 东方财富资金流 |
| raw_moneyflow_ths | 82万 | 同花顺资金流 |
| raw_moneyflow_mkt_dc | 561 | 大盘资金流 |
| raw_hsgt_top10 | 2.9万 | 沪深股通十大成交 |
| raw_hsgt_individual | 1698 | 个股北向资金 |
| raw_margin_detail | 340万 | 融资融券明细 |
| raw_margin_total | 3845 | 融资融券总量 |
| raw_macro_indicator | 18.9万 | 雪球/微博情绪+宏观(今天新增) |
| raw_peer_comparison | 5708 | 同行比较(今天新增) |
| raw_stock_cxg | 1083 | 创新高(今天新增) |

### 2.3 基本面/估值层
| 表 | 行数 | 内容 |
|----|------|------|
| raw_financial_indicator | 1.25万 | 财务指标(ROE/ROA/EPS等) |
| raw_daily_basic | 23万 | 日频指标(PE/PB/总市值/换手率) |
| raw_income | 23万 | 利润表 |
| raw_balance_sheet | 22万 | 资产负债表 |
| raw_cashflow | 22万 | 现金流量表 |
| raw_forecast | 8.1万 | 业绩预告 |
| raw_express | 2.2万 | 业绩快报 |
| raw_analyst_forecast | 2334 | 分析师预测 |
| raw_analyst_rank | 200 | 分析师排名 |
| raw_analyst_detail | 852 | 分析师详情 |

### 2.4 技术/因子层
| 表 | 行数 | 内容 |
|----|------|------|
| raw_stk_factor_pro | 918万 | Tushare 专业因子(含 barra) |
| raw_stk_factor | 76万 | Tushare 日频因子 |
| raw_stk_nineturn | 409万 | 九转指标 |
| raw_idx_factor_pro | 477万 | 指数专业因子 |
| raw_cyq_perf | 885万 | 筹码分布 |
| raw_daily_basic | 23万 | 日频基础(换手率/量比等) |
| raw_stk_limit | 946万 | 涨跌停数据 |

### 2.5 指数/权重层
| 表 | 行数 | 内容 |
|----|------|------|
| raw_index_weight | 1638万 | 指数权重(沪深300/中证500等) |
| raw_index_member | 5834 | 指数成分 |
| ref_index_classify | 511 | 申万行业分类 |
| raw_index_dailybasic | 2.7万 | 指数日频估值(VaR/PE/PB) |

### 2.6 衍生品层
| 表 | 行数 | 内容 |
|----|------|------|
| raw_opt_daily | 2365万 | 期权日频 |
| raw_fut_daily | 15万 | 期货日频 |
| raw_foreign_futures | 2.1万 | 外盘期货 |
| raw_cb_daily | 15万 | 可转债日频 |
| raw_hs300_option | 66 | 300ETF 期权 |

### 2.7 宏观/另类层（今天新增为主）
| 表 | 行数 | 内容 |
|----|------|------|
| raw_macro_indicator | 18.9万 | v10+v11+v13+v14: 宏观高频+收益率+情绪 |
| raw_commodity_logistics | 9.1万 | v9: 商品/物流/糖指数 |
| raw_shipping_index | 1.6万 | BDI 等航运 |
| raw_commodity_price | 4466 | 商品价格 |
| raw_global_macro | 5486 | 全球宏观 |
| raw_qvix | 5344 | 恐慌指数 |
| raw_epu_index | 347 | 经济政策不确定性 |

---

## 3. 因子分类体系

### Category 1: value — 价值/估值
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `pe_ttm` | raw_daily_basic | 滚动市盈率 |
| `pb_lf` | raw_daily_basic | 市净率(最新财报) |
| `ps_ttm` | raw_daily_basic | 市销率 |
| `ep_ttm` | 1/pe_ttm | 盈利收益率 |
| `bm` | 1/pb_lf | 账面市值比 |
| `ocf_ev` | raw_cashflow + raw_daily_basic | 经营现金流/企业价值 |
| `div_yield` | raw_daily_basic | 股息率 |
| `pe_peer_pct` | raw_peer_comparison | 行业内PE分位 |

### Category 2: momentum — 动量/反转
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `ret_1m` | raw_stock_daily | 过去1月收益率(跳过最近1天) |
| `ret_3m` | raw_stock_daily | 过去3月收益率 |
| `ret_6m` | raw_stock_daily | 过去6月收益率 |
| `ret_12m_1m` | raw_stock_daily | 12-1月动量(经典动量) |
| `ret_1m_reverse` | raw_stock_daily | 过去1月反转(含最近1天) |
| `max_ret_1m` | raw_stock_daily | 月内最大日收益 |
| `wgt_ret_1m` | raw_stock_daily | 加权收益率(近重远轻) |

### Category 3: volatility — 波动/风险
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `vol_1m` | raw_stock_daily | 21日年化波动率 |
| `vol_3m` | raw_stock_daily | 63日年化波动率 |
| `downside_vol_1m` | raw_stock_daily | 下行波动率 |
| `skew_1m` | raw_stock_daily | 日收益偏度 |
| `beta_1y` | raw_stock_daily + raw_index_daily | 贝塔(对沪深300) |
| `idiosyncratic_vol` | 同上 | 特质波动率(CAPM残差) |
| `var_5pct` | raw_stock_daily | 5% VaR |

### Category 4: quality — 质量/盈利
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `roe_ttm` | raw_financial_indicator | ROE(TTM) |
| `roa_ttm` | raw_financial_indicator | ROA(TTM) |
| `gross_margin` | raw_income | 毛利率 |
| `net_margin` | raw_income | 净利率 |
| `asset_turnover` | raw_financial_indicator | 资产周转率 |
| `accruals` | raw_balance_sheet + raw_cashflow | 应计利润(BS-CF) |
| `debt_to_equity` | raw_financial_indicator | 负债权益比 |
| `interest_coverage` | raw_financial_indicator | 利息覆盖倍数 |
| `dupont_roe` | raw_peer_comparison | 杜邦分析 ROE |
| `profit_stability` | raw_income | 盈利稳定性(5年EPS标准差) |

### Category 5: growth — 成长性
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `revenue_growth_yoy` | raw_financial_indicator | 营收同比增长 |
| `earnings_growth_yoy` | raw_financial_indicator | 净利润同比增长 |
| `eps_growth_3y` | raw_peer_comparison | EPS 3年复合增长 |
| `asset_growth_yoy` | raw_financial_indicator | 总资产同比增长 |
| `earnings_surprise` | raw_forecast + raw_express | 业绩超预期幅度 |
| `forecast_revision` | raw_analyst_forecast | 分析师上调幅度 |

### Category 6: sentiment — 情绪/关注度
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `xq_attention` | raw_macro_indicator (xq_hot_follow) | 雪球关注数 |
| `xq_discussion` | raw_macro_indicator (xq_hot_tweet) | 雪球讨论数 |
| `xq_deal_heat` | raw_macro_indicator (xq_hot_deal) | 雪球交易热度 |
| `attention_delta_1w` | xq_attention 差分 | 关注度周变化(核心alpha) |
| `discussion_burst` | xq_discussion Z-score | 讨论异动 |
| `analyst_rating` | raw_analyst_detail + raw_analyst_rank | 分析师综合评级 |
| `northbound_flow_ratio` | raw_hsgt_individual | 北向资金占比变化 |

### Category 7: liquidity — 流动性/规模
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `ln_market_cap` | raw_daily_basic | 对数总市值 |
| `turnover_1m` | raw_stock_daily | 月均换手率 |
| `turnover_cv` | raw_stock_daily | 换手率变异系数 |
| `amihud_illiq` | raw_stock_daily | Amihud 非流动性 |
| `dollar_volume_1m` | raw_stock_daily | 月均成交额 |
| `share_float_ratio` | raw_share_float | 流通股本占比 |

### Category 8: macro_state — 宏观/市场状态
| 因子 | 数据源 | 定义 |
|------|--------|------|
| `market_pe_pct` | raw_index_dailybasic | 沪深300 PE 历史分位 |
| `market_pb_pct` | raw_index_dailybasic | 沪深300 PB 历史分位 |
| `cn_us_spread` | raw_macro_indicator (cn_bond_*) | 中美10Y利差 |
| `bdi_momentum` | raw_commodity_logistics | BDI 3月动量 |
| `qvix_level` | raw_qvix | 50ETF 恐慌指数 |
| `new_high_ratio` | raw_stock_cxg | 创新高占比 |
| `margin_balance_ratio` | raw_margin_total | 融资余额/流通市值 |

---

## 4. 模块结构

```
src/factors/
├── __init__.py          # 因子注册 & 统一接口
├── value.py             # 价值/估值因子
├── momentum.py          # 动量/反转因子
├── volatility.py        # 波动/风险因子
├── quality.py           # 质量/盈利因子
├── growth.py            # 成长性因子
├── sentiment.py         # 情绪/关注度因子
├── liquidity.py         # 流动性/规模因子
├── macro_state.py       # 宏观/市场状态因子
└── utils.py             # 共享工具函数(标准化/去极值/中性化)
```

每个模块的函数签名：
```python
def <factor_name>(start_date=None, end_date=None) -> pd.DataFrame:
    """
    Returns: DataFrame with index=date, columns=ts_code, values=factor_value
    """
```

## 5. 实现优先级

### Phase 1: 核心因子（本周）—— 数据最干净、学界验证最强的 12 个
1. `pe_ttm`, `pb_lf` (价值) — 来源 raw_daily_basic
2. `ret_1m`, `ret_12m_1m` (动量) — 来源 raw_stock_daily
3. `vol_1m`, `beta_1y` (风险) — 来源 raw_stock_daily
4. `roe_ttm`, `accruals` (质量) — 来源 raw_financial_indicator
5. `revenue_growth_yoy` (成长) — 来源 raw_financial_indicator
6. `xq_attention_delta_1w` (情绪) — 来源 raw_macro_indicator ⭐
7. `ln_market_cap`, `turnover_1m` (流动性) — 来源 raw_daily_basic

### Phase 2: 扩展因子（下周）
- 剩余 8 大类全部铺满，~40 个因子

### Phase 3: 衍生/合成因子
- 中性化(行业+市值)版本
- 因子组合/rank 合成

## 6. 数据流

```
raw_tables → factor_func() → standardized_factor → backtest_engine
                              ↓
                         factor_store (parquet)
```

输出格式统一为 parquet: `data/factors/{factor_name}.parquet`
索引: (trade_date, ts_code)，值: factor_value
