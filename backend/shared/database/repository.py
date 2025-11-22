"""
Repository for Job model operations.

Provides high-level CRUD operations for the Jobs table.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import Job, JobStatus, JobType


class JobRepository:
    """Repository for Job database operations."""

    @staticmethod
    def create_job(
        session: Session,
        job_id: str,
        job_type: JobType,
        request_payload: dict[str, Any],
        parent_job_id: str | None = None,
    ) -> Job:
        """
        Create a new job.

        Args:
            session: Database session
            job_id: Unique job identifier
            job_type: Type of job
            request_payload: Job input data
            parent_job_id: Parent job ID for multi-step workflows

        Returns:
            Created Job instance
        """
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
        """
        Get job by ID.

        Args:
            session: Database session
            job_id: Job identifier

        Returns:
            Job instance or None if not found
        """
        return session.query(Job).filter(Job.job_id == job_id).first()

    @staticmethod
    def update_job_status(
        session: Session,
        job_id: str,
        status: JobStatus,
        error_message: str | None = None,
    ) -> Job | None:
        """
        Update job status.

        Args:
            session: Database session
            job_id: Job identifier
            status: New status
            error_message: Error message if status is FAILED

        Returns:
            Updated Job instance or None if not found
        """
        job = session.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = status
            job.updated_at = datetime.now(timezone.utc)

            if error_message:
                job.error_message = error_message

            if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                job.completed_at = datetime.now(timezone.utc)

            session.flush()
        return job

    @staticmethod
    def update_job_response(
        session: Session,
        job_id: str,
        response_payload: dict[str, Any],
        status: JobStatus = JobStatus.COMPLETED,
    ) -> Job | None:
        """
        Update job with response data.

        Args:
            session: Database session
            job_id: Job identifier
            response_payload: Job output data
            status: Job status (default: COMPLETED)

        Returns:
            Updated Job instance or None if not found
        """
        job = session.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.response_payload = response_payload
            job.status = status
            job.updated_at = datetime.now(timezone.utc)

            if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                job.completed_at = datetime.now(timezone.utc)

            session.flush()
        return job

    @staticmethod
    def increment_retry_count(session: Session, job_id: str) -> Job | None:
        """
        Increment job retry count.

        Args:
            session: Database session
            job_id: Job identifier

        Returns:
            Updated Job instance or None if not found
        """
        job = session.query(Job).filter(Job.job_id == job_id).first()
        if job:
            current_count = int(job.retry_count or "0")
            job.retry_count = str(current_count + 1)
            job.updated_at = datetime.now(timezone.utc)
            session.flush()
        return job

    @staticmethod
    def get_jobs_by_status(
        session: Session,
        status: JobStatus,
        limit: int = 100,
    ) -> list[Job]:
        """
        Get jobs by status.

        Args:
            session: Database session
            status: Job status to filter by
            limit: Maximum number of jobs to return

        Returns:
            List of Job instances
        """
        return (
            session.query(Job)
            .filter(Job.status == status)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_jobs_by_type(
        session: Session,
        job_type: JobType,
        limit: int = 100,
    ) -> list[Job]:
        """
        Get jobs by type.

        Args:
            session: Database session
            job_type: Job type to filter by
            limit: Maximum number of jobs to return

        Returns:
            List of Job instances
        """
        return (
            session.query(Job)
            .filter(Job.type == job_type)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_child_jobs(session: Session, parent_job_id: str) -> list[Job]:
        """
        Get all child jobs for a parent job.

        Args:
            session: Database session
            parent_job_id: Parent job identifier

        Returns:
            List of child Job instances
        """
        return (
            session.query(Job)
            .filter(Job.parent_job_id == parent_job_id)
            .order_by(Job.created_at.asc())
            .all()
        )
