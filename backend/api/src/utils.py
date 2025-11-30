"""
Utility functions for the Backend API service.

Contains shared utilities used across different modules.
"""

from typing import Any


def create_planning_payload(job_id: str, user_query: str, user_id: str | None = None) -> dict[str, Any]:
    """
    Create standardized payload for planning jobs.

    This utility ensures consistent payload structure across local HTTP calls
    and production SQS messages to the Planner Agent.

    Args:
        job_id: Unique identifier for the job
        user_query: The user's query to be processed
        user_id: Optional user identifier

    Returns:
        Standardized payload dictionary
    """
    return {
        "job_id": job_id,
        "user_id": user_id,
        "request_payload": {
            "user_query": user_query,
        },
    }
