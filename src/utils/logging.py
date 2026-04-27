"""Logging configuration."""

from __future__ import annotations

import logging
import sys

from src.config.settings import settings


def setup_logging():
    """Configure root logger with structured format."""
    level = getattr(logging, settings.log.level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-30s | %(levelname)-5s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
