"""De-duplication utilities."""

from __future__ import annotations

from typing import Any, Callable, Hashable


def dedup_by_key(
    records: list[dict[str, Any]],
    key_fn: Callable[[dict[str, Any]], Hashable],
    keep: str = "first",
) -> list[dict[str, Any]]:
    """Deduplicate a list of dicts by a key function.

    Args:
        records: List of dictionaries.
        key_fn: Function returning a hashable key for each record.
        keep: 'first' or 'last'.

    Returns:
        Deduplicated list preserving original order.
    """
    seen: set[Hashable] = set()
    result = []

    if keep == "first":
        for rec in records:
            key = key_fn(rec)
            if key not in seen:
                seen.add(key)
                result.append(rec)
    elif keep == "last":
        for rec in reversed(records):
            key = key_fn(rec)
            if key not in seen:
                seen.add(key)
                result.append(rec)
        result.reverse()
    else:
        raise ValueError(f"keep must be 'first' or 'last', got '{keep}'")

    return result
