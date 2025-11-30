"""
Repository for Job model operations.

Provides high-level CRUD operations for the Jobs table.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import Job, JobStatus, JobType


class JobRepository:
    """Simple repository for Job database operations."""

    @staticmethod
    def create_job(
        session: Session,
        job_id: str,
        job_type: JobType,
        request_payload: dict[str, Any],
        parent_job_id: str | None = None,
    ) -> Job:
        """Create a new job."""
        job = Job(
            job_id=job_id,
            type=job_type,
            status=JobStatus.PENDING,
            request_payload=request_payload,
            parent_job_id=parent_job_id,
        )
        session.add(job)
        session.flush()
        return job

    @staticmethod
    def get_job(session: Session, job_id: str) -> Job | None:
        """Get job by ID."""
        return session.query(Job).filter(Job.job_id == job_id).first()

    @staticmethod
    def update_job(
        session: Session,
        job_id: str,
        status: JobStatus | None = None,
        response_payload: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> Job | None:
        """Update job fields."""
        job = session.query(Job).filter(Job.job_id == job_id).first()
        if job:
            if status:
                job.status = status
            if response_payload is not None:
                job.response_payload = response_payload
            if error_message:
                job.error_message = error_message
            job.updated_at = datetime.now(timezone.utc)
            session.flush()
        return job

    @staticmethod
    def get_child_jobs(session: Session, parent_job_id: str) -> list[Job]:
        """Get all child jobs for a parent job."""
        return (
            session.query(Job)
            .filter(Job.parent_job_id == parent_job_id)
            .order_by(Job.created_at.asc())
            .all()
        )
