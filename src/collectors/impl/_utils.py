"""Shared utility functions for collectors."""

from typing import Any, Optional


def _f(v: Any) -> Optional[float]:
    """Safe float conversion.

    Returns None for None/empty/invalid values.
    Used by multiple collectors for field normalization.
    """
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None
