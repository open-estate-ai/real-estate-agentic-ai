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
        Invokes the legal agent to create a plan based on the job ID in the context.

        Args:
            wrapper (RunContextWrapper[PlannerContext]): The run context wrapper containing the planner context.

        Returns:
            str: The response from the legal agent.
        """
        print("🔧 Invoking Legal Agent Tool...")
        job_id = wrapper.context.job_id
        payload = {
            "job_id": wrapper.context.job_id,
        }

        if ENV == "local":
            print(
                f"🔧 Invoking Legal Agent locally at {LEGAL_AGENT_URL} for job {job_id}")
            return await HttpClient.post(
                host=LEGAL_AGENT_URL,
                path="/legal-agent",
                payload=payload
            )
        else:
            print(f"🔧 Invoking Legal Agent via Lambda for job {job_id}")
            lambda_client = LambdaClient()
            return await lambda_client.invoke_lambda_agent(
                agent_name="legal-agent",
                function_name=LEGAL_AGENT_FUNCTION_NAME,
                payload=payload,
            )
