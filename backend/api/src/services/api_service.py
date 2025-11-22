import logging
from typing import Any

from database import JobRepository, JobStatus, JobType, get_db_session
from sqlalchemy import text


logger = logging.getLogger(__name__)


class ApiService:
    @staticmethod
    def check_database_health() -> str:
        """Check database connectivity."""
        try:
            with get_db_session() as session:
                session.execute(text("SELECT 1"))
            return "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return f"unhealthy: {str(e)}"

    @staticmethod
    def get_job_details(job_id: str) -> dict[str, Any] | None:
        """Get job details by ID."""
        with get_db_session() as session:
            job = JobRepository.get_job(session=session, job_id=job_id)
            return job.to_dict() if job else None

    @staticmethod
    def get_job_children(job_id: str) -> list[dict[str, Any]]:
        """Get all child jobs for a parent job."""
        with get_db_session() as session:
            children = JobRepository.get_child_jobs(
                session=session, parent_job_id=job_id)
            return [child.to_dict() for child in children]
