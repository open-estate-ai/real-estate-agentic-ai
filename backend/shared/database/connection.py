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
# AWS SSM PARAMETER STORE FOR CREDENTIALS
# =============================================================================


def _get_ssm_parameter(parameter_name: str, decrypt: bool = False) -> str:
    """
    Get parameter value from AWS SSM Parameter Store.

    Args:
        parameter_name: SSM parameter name
        decrypt: Whether to decrypt SecureString parameters

    Returns:
        str: Parameter value

    Raises:
        Exception: If parameter retrieval fails
    """
    import boto3

    region = os.getenv("AWS_REGION", "us-east-1")
    ssm_client = boto3.client('ssm', region_name=region)

    try:
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=decrypt
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"[DB] Error retrieving SSM parameter {parameter_name}: {e}")
        raise


def _get_aws_db_credentials() -> tuple[str, str]:
    """
    Get database credentials from AWS SSM Parameter Store.

    Returns:
        tuple: (username, password)

    Raises:
        Exception: If credential retrieval fails
    """
    env = os.getenv("ENV", "dev")
    ssm_prefix = f"/{env}/{env}-open-estate-ai"

    print(f"[DB] Fetching credentials from SSM Parameter Store...")
    username = _get_ssm_parameter(f"{ssm_prefix}/db/username", decrypt=False)
    password = _get_ssm_parameter(f"{ssm_prefix}/db/password", decrypt=True)

    print(f"[DB] Retrieved credentials for user: {username}")
    return username, password

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
        - Connects to AWS RDS Serverless with password authentication
        - Credentials retrieved from SSM Parameter Store
        - postgresql://user:pass@rds-serverless-endpoint:5432/dbname?sslmode=require

    Returns:
        str: Database connection URL
    """
    if IS_LOCAL:
        # LOCAL: Existing way - Docker PostgreSQL with password
        url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"[DB] LOCAL: Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}")
    else:
        # AWS LAMBDA: RDS Serverless with password auth from SSM Parameter Store
        username, password = _get_aws_db_credentials()
        url = f"postgresql://{username}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
        print(f"[DB] AWS LAMBDA ({ENV}): Connecting to RDS Serverless")
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
            # AWS LAMBDA: Serverless-optimized configuration with password auth
            lambda_pool_size = int(os.getenv("DB_POOL_SIZE", "2"))
            lambda_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

            engine_config = {
                "pool_size": lambda_pool_size,
                "max_overflow": 0,  # No overflow for Lambda
                "pool_timeout": 10,  # Fast timeout
                "pool_recycle": lambda_pool_recycle,  # Recycle connections
                "pool_pre_ping": True,  # Verify before use
                "echo": os.getenv("DB_ECHO", "false").lower() == "true",
                # SSL required for RDS
                "connect_args": {"sslmode": "require"},
            }

            _engine = create_engine(DATABASE_URL, **engine_config)
            print(f"[DB] Engine created: pool_size={lambda_pool_size}, "
                  f"pool_recycle={lambda_pool_recycle}s, password_auth=true")

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
