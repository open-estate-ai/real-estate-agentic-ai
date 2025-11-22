"""
Database models shared across all agents.

All agent Lambda functions interact with the same database tables.
"""

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Type of agent job."""

    INTENT_CLASSIFICATION = "intent_classification"
    PLANNING = "planning"
    SEARCH = "search"
    VALUATION = "valuation"
    LEGAL_CHECK = "legal_check"
    VERIFICATION = "verification"
    SUMMARIZATION = "summarization"


class Job(Base):
    """
    Jobs table - tracks all agent task executions.

    Each agent picks up jobs from SQS, updates this table with status,
    and stores results in the request_payload or a separate results field.
    """

    __tablename__ = "jobs"

    # Primary key
    job_id = Column(
        String(255),
        primary_key=True,
        nullable=False,
        comment="Unique job identifier (UUID or SQS message ID)",
    )

    # Job metadata
    type = Column(
        Enum(JobType),
        nullable=False,
        index=True,
        comment="Type of agent job",
    )

    status = Column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
        comment="Current job status",
    )

    # Request data
    request_payload = Column(
        JSON,
        nullable=False,
        comment="Input data for the job (query, parameters, context)",
    )

    # Response data
    response_payload = Column(
        JSON,
        nullable=True,
        comment="Output data from the job (results, errors, metadata)",
    )

    # Error tracking
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if job failed",
    )

    retry_count = Column(
        String(10),
        default="0",
        comment="Number of retry attempts",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When the job was created",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="When the job was last updated",
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the job completed or failed",
    )

    # Parent job relationship (for multi-step workflows)
    parent_job_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Parent job ID for multi-step workflows",
    )

    def __repr__(self) -> str:
        return f"<Job(job_id={self.job_id}, type={self.type}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            "request_payload": self.request_payload,
            "response_payload": self.response_payload,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parent_job_id": self.parent_job_id,
        }
