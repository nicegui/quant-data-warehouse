# Architecture

## Data Flow

```
+----------------+     +---------+     +----------+     +-----------+
|   API Source   | --> |  RAW    | --> | CURATED  | --> |  PARQUET  |
| (Tushare/CCXT) |     | (PG)    |     | (PG)     |     | (Hive)    |
+----------------+     +---------+     +----------+     +-----------+
                             |               |               |
                       append-only      SCD2 v2       col-store
                       immutable        adj prices     DuckDB/Polars
```

## Layer Definitions

### Raw (raw_*)
- Direct API response dump
- Append-only, never modified
- Preserves all original fields
- Enables full traceability

### Curated (curated_*)
- Cleaned, validated, adjusted
- Forward-adjusted (前复权) for stocks
- SCD2 for historical revisions
- Optimized for query performance

### Reference (ref_*)
- Stock basic info, trade calendar, adj factors
- Replaced periodically (not time-series)
- Small tables, frequently joined

### Parquet Export (data/parquet/)
- Hive-partitioned directory layout
- Columnar storage for fast analytics
- Readable by DuckDB, Polars, Pandas
- One-click sync to NAS/cloud

## Unified Asset ID

Every tradable entity gets a UUID. All curated tables reference
asset_id instead of ts_code/symbol, enabling cross-asset queries.

## Scheduling

- APScheduler-based, reads config from YAML
- Each source has its own cron schedule
- Pipeline audit logs track every run
- Failed runs trigger exponential backoff retry
