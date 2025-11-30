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

    async def invoke_lambda_agent(
        agent_name: str, function_name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke a Lambda function for an agent."""

        # For local testing with mocked agents
        if MOCK_LAMBDAS:
            logger.info(
                f"[MOCK] Would invoke {agent_name} with payload: {json.dumps(payload)[:200]}")
            return {"success": True, "message": f"[Mock] {agent_name} completed", "mock": True}

        try:
            logger.info(f"Invoking {agent_name} Lambda: {function_name}")
            lambda_client = LambdaClient._get_lambda_client()
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )

            result = json.loads(response["Payload"].read())

            # Unwrap Lambda response if it has the standard format
            if isinstance(result, dict) and "statusCode" in result and "body" in result:
                if isinstance(result["body"], str):
                    try:
                        result = json.loads(result["body"])
                    except json.JSONDecodeError:
                        result = {"message": result["body"]}
                else:
                    result = result["body"]

            logger.info(f"{agent_name} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error invoking {agent_name}: {e}")
            return {"error": str(e)}
