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
        user_query: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send query to planner agent to create execution plan.

        Args:
            job_id: Unique job identifier
            user_query: User's query
            user_id: Optional user identifier

        Returns:
            Response from planner agent

        Raises:
            httpx.HTTPError: If request fails
        """
        logger.info(
            f"Sending request to planner agent: {self.base_url}/user-query")
        logger.debug(f"Job ID: {job_id}, Query: {user_query}, User: {user_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/user-query",
                json={
                    "job_id": job_id,
                    "user_id": user_id,
                    "request_payload": {
                        "user_query": user_query,
                    },
                },
                timeout=self.timeout,
            )

            if response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_response = response.json()
                    error_detail = error_response.get(
                        'detail', str(error_response))
                except:
                    error_detail = response.text

                logger.error(
                    f"Planner agent error {response.status_code}: {error_detail}")
                response.raise_for_status()

            result = response.json()

            logger.info(
                f"Received response from planner agent: status={response.status_code}")
            logger.debug(f"Response data: {result}")

            return result
