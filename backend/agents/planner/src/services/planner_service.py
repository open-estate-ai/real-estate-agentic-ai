"""
Planner Service - Business logic for planning agent.

This service layer sits between the API/Lambda handler and the repository layer.
It handles the core business logic for creating plans and managing jobs.
"""

import uuid
from typing import Any

from database import JobRepository, JobStatus, JobType, get_db_session
from ..planner import create_plan


class PlannerService:
    """Service for planning operations."""

    @staticmethod
    async def create_plan_for_query(
        job_id: str,
        user_query: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create execution plan for a user query.

        Args:
            job_id: Unique job identifier
            user_query: User's natural language query
            user_id: Optional user identifier

        Returns:
            Plan with job details
        """
        # Create planning job with status RUNNING immediately
        with get_db_session() as session:
            JobRepository.create_job(
                session=session,
                job_id=job_id,
                job_type=JobType.PLANNING,
                request_payload={
                    "user_query": user_query,
                },
            )

            # Set to running status immediately
            JobRepository.update_job(
                session=session,
                job_id=job_id,
                status=JobStatus.IN_PROGRESS,
            )

        try:
            # Generate plan using LLM
            plan = await create_plan(user_query, {})

            # Update job with completed plan (no child jobs)
            with get_db_session() as session:
                JobRepository.update_job(
                    session=session,
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    response_payload={
                        "plan": plan,
                        "user_id": user_id,
                    },
                )

            return {
                "job_id": job_id,
                "plan": plan,
                "user_id": user_id,
            }

        except Exception as e:
            # Mark job as failed
            with get_db_session() as session:
                JobRepository.update_job(
                    session=session,
                    job_id=job_id,
                    status=JobStatus.FAILED,
                    error_message=str(e),
                )
            raise

    # @staticmethod
    # def get_job_details(job_id: str) -> dict[str, Any] | None:
    #     """Get job details by ID."""
    #     with get_db_session() as session:
    #         job = JobRepository.get_job(session=session, job_id=job_id)
    #         return job.to_dict() if job else None

    # @staticmethod
    # def get_job_children(job_id: str) -> list[dict[str, Any]]:
    #     """Get all child jobs for a parent job."""
    #     with get_db_session() as session:
    #         children = JobRepository.get_child_jobs(
    #             session=session, parent_job_id=job_id)
    #         return [child.to_dict() for child in children]
