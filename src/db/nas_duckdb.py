"""DuckDB HTTP client for NAS remote database.

Routes collector writes through HTTP to the NAS DuckDB server
instead of local SQLAlchemy + DuckDB file.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, Optional

import requests

from src.config.settings import settings

logger = logging.getLogger(__name__)

# NAS DuckDB server URL (from env or default)
NAS_URL = settings.db.duckdb_http_url
_TIMEOUT = 30  # seconds

# YYYYMMDD compact date pattern (Tushare style)
_COMPACT_DATE = re.compile(r"^\d{8}$")
# YYYYMMDD HH:MM:SS compact datetime (Tushare style)
_COMPACT_DATETIME = re.compile(r"^\d{8}\s+\d{2}:\d{2}(:\d{2}(\.\d+)?)?$")


def _normalize_date(val: Any) -> Any:
    """Convert Tushare-style compact date strings to ISO format for DuckDB.

    '20260604' → '2026-06-04'
    '20260604 09:30:00' → '2026-06-04 09:30:00'
    """
    if not isinstance(val, str):
        return val
    if _COMPACT_DATE.match(val):
        return f"{val[:4]}-{val[4:6]}-{val[6:8]}"
    if _COMPACT_DATETIME.match(val):
        return f"{val[:4]}-{val[4:6]}-{val[6:8]}{val[8:]}"
    return val


def _serialize_value(val: Any) -> Any:
    """Convert Python types to JSON-serializable values for DuckDB."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, str):
        return _normalize_date(val)
    # Fallback: stringify
    return str(val)


def _serialize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialize all values in a list of record dicts."""
    return [
        {k: _serialize_value(v) for k, v in rec.items()}
        for rec in records
    ]


def is_available() -> bool:
    """Check if the NAS DuckDB server is reachable."""
    try:
        r = requests.get(f"{NAS_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def upsert(table: str, records: list[dict[str, Any]], dedup_keys: list[str]) -> dict:
    """Upsert records via HTTP /upsert endpoint.

    Args:
        table: DuckDB table name (from model.__tablename__)
        records: list of record dicts
        dedup_keys: unique key field names

    Returns:
        {"written": int, "skipped": int}
    """
    if not records:
        return {"written": 0, "skipped": 0}
    serialized = _serialize_records(records)
    payload = {
        "table": table,
        "records": serialized,
        "dedup_keys": dedup_keys,
    }
    r = requests.post(f"{NAS_URL}/upsert", json=payload, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def insert(table: str, records: list[dict[str, Any]]) -> dict:
    """Insert records via HTTP /insert endpoint."""
    if not records:
        return {"written": 0}
    serialized = _serialize_records(records)
    payload = {"table": table, "records": serialized}
    r = requests.post(f"{NAS_URL}/insert", json=payload, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def query(sql: str) -> list[dict]:
    """Run a SELECT query via HTTP /query endpoint.

    Returns:
        List of row dicts, e.g. [{"col1": val1, "col2": val2}, ...]
        Empty list if no rows.
    """
    payload = {"query": sql}
    r = requests.post(f"{NAS_URL}/query", json=payload, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    columns = data.get("columns", [])
    rows = data.get("rows", [])
    return [dict(zip(columns, row)) for row in rows]


def exec_sql(sql: str) -> dict:
    """Execute DDL/DML via HTTP /exec endpoint."""
    payload = {"sql": sql}
    r = requests.post(f"{NAS_URL}/exec", json=payload, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def tables() -> list[str]:
    """List all tables in the remote database."""
    r = requests.get(f"{NAS_URL}/tables", timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json().get("tables", [])


def schema(table: str) -> dict:
    """Get column definitions for a table."""
    r = requests.get(f"{NAS_URL}/schema/{table}", timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()
