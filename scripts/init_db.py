#!/usr/bin/env python3
"""Initialize the database - create all tables and run Alembic migrations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import settings
from src.db.engine import get_engine
from src.models.base import Base
from src.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("init_db")


def main():
    logger.info("Initializing database: %s@%s/%s",
                 settings.db.user, settings.db.host, settings.db.db)

    engine = get_engine()

    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully")

    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info("Tables in database: %s", ", ".join(sorted(tables)))


if __name__ == "__main__":
    main()
