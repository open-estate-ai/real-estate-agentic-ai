"""
Planner logic - creates execution plans using LLM.
"""

import os
from typing import Any

from litellm import acompletion


async def create_plan(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """
    Create an execution plan for a user query using LLM.

    Args:
        query: User's natural language query
        context: Additional context (user preferences, history, etc.)

    Returns:
        Plan dictionary with steps and metadata
    """

    llm_model = os.getenv("LLM_MODEL", "gpt-4")

    system_prompt = """You are a planning agent for a real estate AI system.
Your job is to analyze user queries and create a step-by-step execution plan.

Available agents:
- SEARCH: Find property listings based on criteria
- VALUATION: Estimate property values and comparables
- LEGAL_CHECK: Verify legal compliance and registry
- VERIFICATION: Check data integrity and fraud signals
- SUMMARIZATION: Create final report for user

Analyze the query and create a plan with these steps.
Return a JSON object with:
{
  "steps": [
    {
      "agent": "SEARCH",
      "action": "find_listings",
      "payload": {"city": "Noida", "bedrooms": 3, "max_price": 10000000}
    },
    ...
  ],
  "reasoning": "Brief explanation of the plan",
  "estimated_duration_seconds": 60
}
"""

    user_prompt = f"""Create an execution plan for this query:

Query: {query}

Context: {context}

Return only valid JSON, no markdown."""

    try:
        response = await acompletion(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        # Extract JSON from response
        content = response.choices[0].message.content

        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        import json
        plan = json.loads(content.strip())

        return plan

    except Exception as e:
        # Fallback to simple search plan
        return {
            "steps": [
                {
                    "agent": "SEARCH",
                    "action": "find_listings",
                    "payload": {"query": query}
                },
                {
                    "agent": "SUMMARIZATION",
                    "action": "create_report",
                    "payload": {"format": "text"}
                }
            ],
            "reasoning": f"Fallback plan due to error: {str(e)}",
            "estimated_duration_seconds": 30,
            "fallback": True,
        }
