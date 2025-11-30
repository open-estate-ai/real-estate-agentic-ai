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
from .services import PlannerService


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for SQS events.

    Expected SQS message body format:
    {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "user-123",
        "request_payload": {
            "user_query": "Find 3BHK apartments in Noida"
        }
    }

    Args:
        event: Lambda event containing SQS records
        context: Lambda context

    Returns:
        Response with processing status
    """
    print(f"📥 Received event: {json.dumps(event)}")

    results = []

    # Process each SQS record
    for record in event.get('Records', []):
        job_id = None  # Initialize job_id for error handling
        try:
            # Extract message details
            message_id = record.get('messageId', str(uuid.uuid4()))
            body = json.loads(record.get('body', '{}'))

            print(f"📋 Processing message {message_id}")
            print(f"📝 Body: {json.dumps(body)}")

            # Extract request data
            job_id = body.get('job_id')
            user_id = body.get('user_id')
            request_payload = body.get('request_payload', {})
            user_query = request_payload.get('user_query')

            if not job_id:
                raise ValueError("Missing 'job_id' in message body")
            if not user_query:
                raise ValueError("Missing 'user_query' in request_payload")

            # Process the planning request
            result = asyncio.run(process_planning_request(
                job_id=job_id,
                user_query=user_query,
                user_id=user_id,
            ))

            results.append({
                "messageId": message_id,
                "job_id": job_id,  # Include generated job_id in response
                "status": "success",
                "result": result,
            })

            print(
                f"✅ Successfully processed message {message_id} with job_id {job_id}")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error processing message: {error_msg}")

            # Try to update job as failed if we have a valid job_id
            try:
                message_id = record.get('messageId', str(uuid.uuid4()))
                # Use job_id if we have one, otherwise generate one
                if job_id is None:
                    job_id = str(uuid.uuid4())

                with get_db_session() as session:
                    JobRepository.update_job(
                        session=session,
                        job_id=job_id,
                        status=JobStatus.FAILED,
                        error_message=error_msg,
                    )
            except Exception:
                pass

            results.append({
                "messageId": record.get('messageId', 'unknown'),
                "status": "error",
                "error": error_msg,
            })

    # Return summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')

    return {
        "statusCode": 200 if error_count == 0 else 207,
        "body": json.dumps({
            "processed": len(results),
            "successful": success_count,
            "failed": error_count,
            "results": results,
        }),
    }


async def process_planning_request(
    job_id: str,
    user_query: str,
    user_id: str | None,
) -> dict[str, Any]:
    """
    Process a planning request.

    This delegates to the service layer for all business logic.

    Args:
        job_id: Unique job identifier
        user_query: User's natural language query
        user_id: User identifier (optional)

    Returns:
        Plan with job details
    """
    result = await PlannerService.create_plan_for_query(
        job_id=job_id,
        user_query=user_query,
        user_id=user_id,
    )
    print(f"✅ Planning completed for job {job_id}")
    print("✅ Plan execution started.")

    await PlannerService.create_execute_plan(
        job_id=job_id
    )

    print(f"✅ Plan execution completed for job {job_id}")
    print(f"✅ Planning completed for job {job_id}")

    return result


# For local testing
if __name__ == "__main__":
    # Sample SQS event for testing
    test_event = {
        "Records": [
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "job_id": str(uuid.uuid4()),
                    "user_id": "test-user-123",
                    "request_payload": {
                        "user_query": "Find 3BHK luxury apartments in Bangalore under 2 crore",
                    }
                })
            }
        ]
    }

    print("🧪 Testing Lambda handler locally...")
    result = lambda_handler(test_event, None)
    print(f"📊 Result: {json.dumps(result, indent=2)}")
