"""Shared utility functions for collectors."""

import math
from typing import Any, Optional


def _f(v: Any, default: Optional[float] = None) -> Optional[float]:
    """Safe float conversion.

    Returns None for None/empty/invalid/NaN values, or *default* when provided.
    Used by multiple collectors for field normalization.
    """
    if v is None or v == "":
        return default
    try:
        result = float(v)
        if math.isnan(result):
            return default
        return result
    except (ValueError, TypeError):
        return default
