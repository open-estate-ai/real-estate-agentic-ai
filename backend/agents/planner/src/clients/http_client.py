"""Simple HTTP client for local agent communication."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class HttpClient:
    """Simple HTTP client for making requests to local agents."""

    @staticmethod
    async def post(
        host: str,
        path: str,
        payload: dict[str, Any],
        timeout: float = 30.0
    ) -> dict[str, Any]:
        """
        Make a POST request to a local agent.

        Args:
            host: The host (e.g., "http://localhost:8082")
            path: The request path (e.g., "/legal-agent")
            payload: Dictionary payload to send
            timeout: Request timeout in seconds

        Returns:
            Response from the agent as a dictionary

        Raises:
            Exception: If the request fails
        """
        url = f"{host}{path}"

        logger.info(f"Making POST request to {url}")
        logger.debug(f"Payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                result = response.json()
                logger.info(
                    f"Request successful - Status: {response.status_code}")
                logger.debug(f"Response: {result}")

                return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} calling {url}: {e}")
            raise Exception(
                f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling {url}: {e}")
            raise Exception(f"Request timeout after {timeout}s")
        except Exception as e:
            logger.error(f"Error calling {url}: {e}")
            raise Exception(f"Request failed: {str(e)}")
