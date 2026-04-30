"""Shared utility functions for collectors."""

from typing import Any, Optional


def _f(v: Any, default: Optional[float] = None) -> Optional[float]:
    """Safe float conversion.

    Returns None for None/empty/invalid values, or *default* when provided.
    Used by multiple collectors for field normalization.
    """
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default
