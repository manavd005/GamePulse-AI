"""
Database Session & Connection Management Module.

Configures SQLAlchemy engine, session maker, base model, and FastAPI dependency generator.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.settings import settings

logger = logging.getLogger("gamepulse.database")

# Create SQLAlchemy Engine
# SQLite requires check_same_thread=False for multithreaded FastAPI worker threads
engine_kwargs = {}
if settings.db.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": settings.db.DB_POOL_SIZE,
        "max_overflow": settings.db.DB_MAX_OVERFLOW,
    })

engine = create_engine(settings.db.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI Dependency Provider for Database Sessions.

    Yields a transactional database session per request and guarantees cleanup/close on completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initializes database tables from SQLAlchemy declarative metadata."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
