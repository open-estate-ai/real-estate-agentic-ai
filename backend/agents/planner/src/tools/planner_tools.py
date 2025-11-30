import os
from agents import function_tool, RunContextWrapper
from .planner_context import PlannerContext
from ..clients.lambda_client import LambdaClient
from ..clients.http_client import HttpClient

ENV = os.getenv("ENV", "local")
LEGAL_AGENT_URL = os.getenv("LEGAL_AGENT_URL", "http://localhost:8082")
LEGAL_AGENT_FUNCTION_NAME = os.getenv(
    "LEGAL_AGENT_FUNCTION_NAME", "legal-agent-function")


class PlannerTools:
    """
    Tools related to planning tasks for the legal agent.
    """

    @function_tool
    async def invoke_legal_agent(wrapper: RunContextWrapper[PlannerContext]) -> str:
        """
        Call the legal agent to analyze real estate queries and provide legal insights.
        Use this tool for any real estate related query that needs legal analysis, property search, or compliance checks.

        This tool handles:
        - Property searches and filtering
        - Legal compliance verification  
        - RERA compliance checks
        - Property documentation analysis

        Args:
            wrapper (RunContextWrapper[PlannerContext]): The run context wrapper containing the planner context.

        Returns:
            str: JSON string with the legal agent's response and analysis.
        """
        print("🔧 Invoking Legal Agent Tool...")
        job_id = wrapper.context.job_id
        payload = {
            "job_id": wrapper.context.job_id,
        }

        if ENV == "local":
            print(
                f"🔧 Invoking Legal Agent locally at {LEGAL_AGENT_URL} for job {job_id}")
            result = await HttpClient.post(
                host=LEGAL_AGENT_URL,
                path="/legal-agent",
                payload=payload
            )
            return str(result)
        else:
            print(f"🔧 Invoking Legal Agent via Lambda for job {job_id}")
            # Call static method directly
            result = await LambdaClient.invoke_lambda_agent(
                agent_name="legal-agent",
                function_name=LEGAL_AGENT_FUNCTION_NAME,
                payload=payload,
            )
            return result  # Already a JSON string from invoke_lambda_agent
