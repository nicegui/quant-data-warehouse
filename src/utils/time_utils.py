"""Time utility functions."""

from __future__ import annotations

from datetime import datetime, timezone

from dateutil import parser


def parse_tushare_date(date_str: str) -> datetime:
    """Parse Tushare date string (YYYYMMDD) to timezone-aware datetime."""
    dt = parser.parse(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_tushare_datetime(dt_str: str) -> datetime:
    """Parse Tushare datetime string to timezone-aware datetime."""
    dt = parser.parse(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def utc_now() -> datetime:
    """Current UTC datetime."""
    return datetime.now(timezone.utc)


def to_tushare_date(dt: datetime) -> str:
    """Convert datetime to Tushare date format (YYYYMMDD)."""
    return dt.strftime("%Y%m%d")
