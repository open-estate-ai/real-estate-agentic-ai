"""
Planner Service - Business logic for planning agent.

This service layer sits between the API/Lambda handler and the repository layer.
It handles the core business logic for creating plans and managing jobs.
"""
import os
import uuid
from typing import Any

from database import JobRepository, JobStatus, JobType, get_db_session
from ..planner import create_plan
from ..tools import PlannerContext, PlannerTools
from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel


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

    @staticmethod
    async def create_execute_plan(
        job_id: str
    ) -> dict[str, Any]:
        """
        Execute the plan by invoking downstream agents.

        Args:
            job_id: The job ID for which to execute the plan

        Returns:
            Dictionary containing execution results
        """
        print(f"🚀 Starting plan execution for job {job_id}")

        try:
            # Get job details from database for input
            with get_db_session() as session:
                job = JobRepository.get_job(session=session, job_id=job_id)

                if not job:
                    raise ValueError(f"Job {job_id} not found")

                # Extract user query for agent input
                user_query = job.request_payload.get("user_query", "")

                print(f"📋 Retrieved job data - Query: '{user_query}'")

            # Create context with only job_id
            context = PlannerContext(job_id=job_id)

            # Setup model and tools
            model_id = os.getenv(
                "LLM_MODEL", "bedrock/openai.gpt-oss-120b-1:0")
            model = LitellmModel(model=f"{model_id}")
            tools = [PlannerTools.invoke_legal_agent]

            PLANNER_INSTRUCTIONS = """
               You are a real estate planning coordinator. For EVERY real estate query, you MUST call the legal agent tool.
               
               IMPORTANT: Always use the invoke_legal_agent tool for ALL real estate queries including:
               - Property searches (apartments, houses, land)
               - Location-based queries (specific cities or areas)
               - Budget-based filtering
               - Legal compliance questions
               - Any real estate related question
               
               DO NOT try to answer directly. ALWAYS invoke the tool first, then provide the response.
            """

            # Create and run agent
            agent = Agent[PlannerContext](
                name="Real Estate Planner",
                instructions=PLANNER_INSTRUCTIONS,
                model=model,
                tools=tools
            )

            print(f"🤖 Running agent with query: '{user_query}'")

            result = await Runner.run(
                agent,
                input=f"Execute the plan for this query: {user_query}",
                context=context,
                max_turns=20
            )

            print(f"✅ Agent execution completed")
            print(f"   Result type: {type(result)}")
            print(f"   Result: {result}")

            # Update job with execution results
            with get_db_session() as session:
                JobRepository.update_job(
                    session=session,
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    response_payload={
                        "plan_execution": {
                            "result": str(result),
                            "all_messages": result.all_messages() if hasattr(result, 'all_messages') else []
                        }
                    }
                )

            return {
                "job_id": job_id,
                "status": "completed",
                "result": str(result)
            }

        except Exception as e:
            print(f"❌ Plan execution failed for job {job_id}: {e}")

            # Update job status to FAILED
            with get_db_session() as session:
                JobRepository.update_job(
                    session=session,
                    job_id=job_id,
                    status=JobStatus.FAILED,
                    error_message=str(e)
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
