"""
Database connection management.

Supports both local PostgreSQL (via Docker) and AWS RDS.
Uses SQLAlchemy for ORM and connection pooling.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# Database configuration from environment variables
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "real_estate_agents")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
# Connection pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Build database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Global engine instance
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """
    Get or create SQLAlchemy engine.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    return _engine


def get_session_maker() -> sessionmaker:
    """
    Get or create SQLAlchemy session maker.

    Returns:
        sessionmaker: Session factory
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
    return _SessionLocal


def get_db_connection() -> Engine:
    """
    Get database connection engine.

    Use this for raw SQL queries or connection testing.

    Returns:
        Engine: SQLAlchemy engine
    """
    return get_engine()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup.

    Use this context manager for all database operations:

    ```python
    with get_db_session() as session:
        job = session.query(Job).filter_by(job_id="123").first()
        job.status = JobStatus.COMPLETED
        session.commit()
    ```

    Yields:
        Session: SQLAlchemy session
    """
    SessionLocal = get_session_maker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database schema.

    Creates all tables defined in models.py if they don't exist.
    This should be run once during deployment or in migrations.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    ⚠️  WARNING: This will delete all data!
    Only use for testing or development.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
