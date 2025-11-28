"""
Planner logic - creates execution plans.

TODO: Implement LLM-based planning logic here.
For now, returns a simple mock plan structure to establish clean app architecture.
"""

from typing import Any


async def create_plan(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """
    Create an execution plan for a user query.

    TODO: Implement proper LLM-based planning here.
    Currently returns a simple mock structure for clean architecture testing.

    Args:
        query: User's natural language query
        context: Additional context (currently unused)

    Returns:
        Plan dictionary with basic structure
    """

    # TODO: Replace with actual LLM logic
    # For now, return a simple mock plan to test the architecture
    return {
        "query_analyzed": query,
        "plan_type": "mock_plan",
        "reasoning": "TODO: Add LLM-based reasoning here",
        "steps": [
            {
                "step_number": 1,
                "description": "Process user query",
                "status": "planned"
            }
        ],
        "estimated_duration_seconds": 5,
        "created_by": "planner_agent_v1",
        "is_mock": True  # Remove when real LLM is implemented
    }
