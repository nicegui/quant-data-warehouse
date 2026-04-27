# Quant Data Warehouse

多源量化数据仓库 — A股、加密币、财报数据的自动化采集、清洗、存储与分析平台。

## 架构

```
采集层 (Collectors) → 原始层 (raw, append-only) → 清洗层 (curated, SCD2) → Parquet导出 → DuckDB分析
```

- **raw 层**: API 原始响应，永不修改，可追溯
- **curated 层**: 清洗后权威数据（前复权、校验、合并），SCD2 慢速变化维度
- **Parquet 层**: Hive 分区列存，Polars/DuckDB 直接分析
- **DuckDB 分析**: 直查 Parquet 极速特征工程与回测

## 快速开始

```bash
# 1. 安装依赖
pip install -e .

# 2. 配置
cp .env.example .env
# 编辑 .env 填入 TUSHARE_TOKEN

# 3. 启动数据库 (PostgreSQL)
docker compose up -d db

# 4. 初始化
python scripts/init_db.py

# 5. 运行采集器
python scripts/run_collector.py stock_daily
python scripts/run_collector.py consultations
```

## 数据源

| 数据源 | 类型 | 状态 |
|--------|------|------|
| Tushare Pro | A股行情、基本面、快讯 | ✅ |
| OKX (CCXT) | 加密币 K 线 | 📦 预留 |
| RSS 快讯 | 新闻资讯 | 📦 预留 |

## 目录结构

```
src/
├── config/          # 配置管理 (Pydantic Settings + YAML)
├── db/              # 数据库引擎 & 会话
├── models/          # SQLAlchemy ORM 模型
├── schemas/         # Pydantic 数据校验
├── collectors/      # 数据采集器
├── pipeline/        # Pipeline 编排 (调度/导出/校验)
└── utils/           # 工具函数
```

## License

MIT
