"""Client for communicating with Planner Agent."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PlannerClient:
    """Client for planner agent communication."""

    def __init__(self):
        self.base_url = os.getenv("PLANNER_AGENT_URL", "http://localhost:8081")
        self.timeout = 30.0

    async def create_plan(
        self,
        job_id: str,
        query: str,
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send query to planner agent to create execution plan.

        Args:
            job_id: Unique job identifier
            query: User's query
            user_id: Optional user identifier
            context: Optional context dictionary

        Returns:
            Response from planner agent

        Raises:
            httpx.HTTPError: If request fails
        """
        logger.info(
            f"Sending request to planner agent: {self.base_url}/user-query")
        logger.debug(f"Job ID: {job_id}, Query: {query}, User: {user_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/user-query",
                json={
                    "job_id": job_id,
                    "query": query,
                    "user_id": user_id,
                    "context": context or {},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"Received response from planner agent: status={response.status_code}")
            logger.debug(f"Response data: {result}")

            return result
