"""
Database connection management.

Supports both local PostgreSQL (via Docker) and AWS RDS Serverless.
Uses SQLAlchemy for ORM and connection pooling.

Environment-based configuration:
- ENV=local: Connects to local Docker PostgreSQL (existing way)
- ENV=dev/stage/production: Connects to AWS RDS Serverless with IAM auth
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================
ENV = os.getenv("ENV", "local")
IS_LOCAL = ENV == "local"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Common database settings
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "real_estate_agents")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")

# Connection pool settings (existing for local)
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# =============================================================================
# AWS RDS SERVERLESS IAM AUTHENTICATION
# =============================================================================


def _get_rds_iam_token() -> str:
    """
    Generate IAM authentication token for RDS Serverless.

    Required for Lambda (ENV != local). No fallback.

    Returns:
        str: Temporary RDS authentication token

    Raises:
        Exception: If IAM token generation fails
    """
    import boto3

    region = os.getenv("AWS_REGION", "us-east-1")

    # Generate RDS IAM token (valid for 15 minutes)
    client = boto3.client('rds', region_name=region)
    token = client.generate_db_auth_token(
        DBHostname=DB_HOST,
        Port=int(DB_PORT),
        DBUsername=DB_USER,
        Region=region
    )
    print(f"[DB] Generated IAM auth token for {DB_USER}@{DB_HOST}")
    return token

# =============================================================================
# DATABASE URL CONSTRUCTION
# =============================================================================


def _build_database_url() -> str:
    """
    Build database URL based on environment.

    Local (ENV=local):
        - Uses existing connection method
        - postgresql://user:pass@localhost:5432/dbname

    AWS Lambda (ENV=dev/stage/production):
        - Connects to AWS RDS Serverless with IAM authentication (ONLY)
        - postgresql://user:token@rds-serverless-endpoint:5432/dbname?sslmode=require

    Returns:
        str: Database connection URL
    """
    if IS_LOCAL:
        # LOCAL: Existing way - Docker PostgreSQL with password
        url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"[DB] LOCAL: Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}")
    else:
        # AWS LAMBDA: RDS Serverless with IAM authentication (ONLY)
        token = _get_rds_iam_token()
        url = f"postgresql://{DB_USER}:{token}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
        print(
            f"[DB] AWS LAMBDA ({ENV}): Connecting to RDS Serverless with IAM auth")
        print(f"[DB] Endpoint: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    return url


# Build database URL at module load time
DATABASE_URL = _build_database_url()

# =============================================================================
# CONNECTION ENGINE
# =============================================================================

# Global engine instance
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """
    Get or create SQLAlchemy engine.

    Local (ENV=local):
        - Uses existing configuration
        - pool_size=5, max_overflow=10
        - Standard PostgreSQL connection

    AWS Lambda (ENV=dev/stage/production):
        - Optimized for serverless + RDS Serverless
        - pool_size=2 (Lambda best practice)
        - pool_recycle=3600 (1 hour - handle RDS connection limits)
        - SSL required for IAM auth

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        if IS_LOCAL:
            # LOCAL: Existing configuration
            _engine = create_engine(
                DATABASE_URL,
                pool_size=POOL_SIZE,
                max_overflow=MAX_OVERFLOW,
                pool_timeout=POOL_TIMEOUT,
                pool_pre_ping=True,
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )
            print(
                f"[DB] Engine created: pool_size={POOL_SIZE}, max_overflow={MAX_OVERFLOW}")
        else:
            # AWS LAMBDA: Serverless-optimized configuration with IAM auth
            lambda_pool_size = int(os.getenv("DB_POOL_SIZE", "2"))
            lambda_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

            engine_config = {
                "pool_size": lambda_pool_size,
                "max_overflow": 0,  # No overflow for Lambda
                "pool_timeout": 10,  # Fast timeout
                "pool_recycle": lambda_pool_recycle,  # Recycle connections
                "pool_pre_ping": True,  # Verify before use
                "echo": os.getenv("DB_ECHO", "false").lower() == "true",
                # SSL required for IAM auth
                "connect_args": {"sslmode": "require"},
            }

            _engine = create_engine(DATABASE_URL, **engine_config)
            print(f"[DB] Engine created: pool_size={lambda_pool_size}, "
                  f"pool_recycle={lambda_pool_recycle}s, iam_auth=true")

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
