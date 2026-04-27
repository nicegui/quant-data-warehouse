"""Retry decorator with exponential backoff."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Optional, Type


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Decorator: retry a function with exponential backoff.

    Args:
        max_attempts: Max retry attempts (default 3).
        delay: Initial delay in seconds (default 1.0).
        backoff: Multiplier for each retry (default 2.0).
        exceptions: Tuple of exception types to catch.
        on_retry: Optional callback (exception, attempt).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        sleep_time = delay * (backoff ** attempt)
                        if on_retry:
                            on_retry(e, attempt + 1)
                        time.sleep(sleep_time)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
