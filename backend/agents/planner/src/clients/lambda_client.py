import json
import os
import boto3
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
MOCK_LAMBDAS = os.getenv("MOCK_LAMBDAS", "false").lower() == "true"


class LambdaClient:
    """Client to interact with AWS Lambda functions."""

    _lambda_client = None

    @classmethod
    def _get_lambda_client(cls):
        """Get or create Lambda client singleton."""
        if cls._lambda_client is None:
            cls._lambda_client = boto3.client('lambda')
        return cls._lambda_client

    @staticmethod
    async def invoke_lambda_agent(
        agent_name: str, function_name: str, payload: Dict[str, Any]
    ) -> str:
        """Invoke a Lambda function for an agent."""

        # For local testing with mocked agents
        if MOCK_LAMBDAS:
            logger.info(
                f"[MOCK] Would invoke {agent_name} with payload: {json.dumps(payload)[:200]}")
            return json.dumps({"success": True, "message": f"[Mock] {agent_name} completed", "mock": True})

        try:
            print(f"🔧 Invoking {agent_name} Lambda: {function_name}")
            print(f"   Payload: {json.dumps(payload)}")

            lambda_client = LambdaClient._get_lambda_client()
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )

            print(
                f"✅ Lambda invocation response status: {response['StatusCode']}")

            result = json.loads(response["Payload"].read())
            print(f"   Response payload: {json.dumps(result)[:500]}")

            # Unwrap Lambda response if it has the standard format
            if isinstance(result, dict) and "statusCode" in result and "body" in result:
                if isinstance(result["body"], str):
                    try:
                        result = json.loads(result["body"])
                    except json.JSONDecodeError:
                        result = {"message": result["body"]}
                else:
                    result = result["body"]

            print(f"✅ {agent_name} completed successfully")
            # Return as JSON string for proper serialization in tool calls
            return json.dumps(result)

        except Exception as e:
            error_msg = f"Error invoking {agent_name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return json.dumps({"error": str(e)})
