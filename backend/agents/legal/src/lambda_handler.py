"""
AWS Lambda handler for Planner Agent.

This module handles SQS events and processes planning requests.
"""

import asyncio
import json
import uuid
from typing import Any
from sqlalchemy import text

from database import JobStatus, get_db_session, init_db, JobRepository


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """

    """
    print(f"📥 Received event: {json.dumps(event)}")

    return {
        "statusCode": 200,
        "body": json.dumps(event),
    }


# For local testing
if __name__ == "__main__":
    # Sample SQS event for testing
    test_event = {
        "Records": [
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "job_id": str(uuid.uuid4())
                })
            }
        ]
    }

    print("🧪 Testing Lambda handler locally...")
    result = lambda_handler(test_event, None)
    print(f"📊 Result: {json.dumps(result, indent=2)}")
