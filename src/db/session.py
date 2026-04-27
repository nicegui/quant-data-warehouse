"""Context-managed database sessions."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from src.db.engine import get_session


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for safe db sessions."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
