"""Client for communicating with Planner Agent."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LocalPlannerClient:
    """Client for local planner agent HTTP communication."""

    def __init__(self):
        self.base_url = os.getenv("PLANNER_AGENT_URL", "http://localhost:8081")
        self.timeout = 30.0

    async def send_planning_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send planning request to local planner agent via HTTP.

        Args:
            payload: Dictionary containing job_id, user_id, and request_payload

        Returns:
            Response from local planner agent

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        job_id = payload.get("job_id")
        user_id = payload.get("user_id")
        user_query = payload.get("request_payload", {}).get("user_query")

        logger.info(
            f"Sending request to planner agent: {self.base_url}/user-query")
        logger.debug(f"Job ID: {job_id}, Query: {user_query}, User: {user_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/user-query",
                json=payload,
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
