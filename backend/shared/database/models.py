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
    """Jobs table - tracks agent task executions."""

    __tablename__ = "jobs"

    job_id = Column(String(255), primary_key=True)
    type = Column(Enum(JobType, values_callable=lambda x: [
                  e.value for e in x]), nullable=False, index=True)
    status = Column(Enum(JobStatus, values_callable=lambda x: [e.value for e in x]), nullable=False,
                    default=JobStatus.PENDING, index=True)
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    parent_job_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(
        timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

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
            "parent_job_id": self.parent_job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
