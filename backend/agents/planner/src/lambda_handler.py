"""
AWS Lambda handler for Planner Agent.

This module handles SQS events and processes planning requests.
"""

from .planner import create_plan
import asyncio
from database import (
    JobRepository,
    JobStatus,
    JobType,
    get_db_session,
    init_db,
)
import json
import os
import uuid
from typing import Any


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for SQS events.

    Expected SQS message body format:
    {
        "query": "Find 3BHK apartments in Noida",
        "user_id": "user-123",
        "context": {
            "budget": 10000000,
            "location": "Noida"
        }
    }

    Args:
        event: Lambda event containing SQS records
        context: Lambda context

    Returns:
        Response with processing status
    """
    print(f"📥 Received event: {json.dumps(event)}")

    # Initialize database on cold start
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Database already initialized or error: {e}")

    results = []

    # Process each SQS record
    for record in event.get('Records', []):
        try:
            # Extract message details
            message_id = record.get('messageId', str(uuid.uuid4()))
            body = json.loads(record.get('body', '{}'))

            print(f"📋 Processing message {message_id}")
            print(f"📝 Body: {json.dumps(body)}")

            # Extract request data
            query = body.get('query')
            user_id = body.get('user_id')
            request_context = body.get('context', {})

            if not query:
                raise ValueError("Missing 'query' in message body")

            # Use message ID as job ID
            job_id = message_id

            # Process the planning request
            result = asyncio.run(process_planning_request(
                job_id=job_id,
                query=query,
                user_id=user_id,
                context=request_context,
            ))

            results.append({
                "messageId": message_id,
                "status": "success",
                "result": result,
            })

            print(f"✅ Successfully processed message {message_id}")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error processing message: {error_msg}")

            # Try to update job as failed
            try:
                message_id = record.get('messageId', str(uuid.uuid4()))
                with get_db_session() as session:
                    JobRepository.update_job_status(
                        session=session,
                        job_id=message_id,
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
    query: str,
    user_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Process a planning request.

    This is the core logic shared between Lambda and FastAPI.

    Args:
        job_id: Unique job identifier
        query: User's natural language query
        user_id: User identifier (optional)
        context: Additional context

    Returns:
        Plan with child job IDs
    """
    # Create parent planning job
    with get_db_session() as session:
        JobRepository.create_job(
            session=session,
            job_id=job_id,
            job_type=JobType.PLANNING,
            request_payload={
                "query": query,
                "user_id": user_id,
                "context": context,
            },
        )

        # Update to in_progress
        JobRepository.update_job_status(
            session=session,
            job_id=job_id,
            status=JobStatus.IN_PROGRESS,
        )

    # Create plan using LLM
    plan = await create_plan(query, context)

    # Create child jobs for each step
    child_job_ids = []
    with get_db_session() as session:
        for step in plan["steps"]:
            child_job_id = f"{job_id}-{step['agent']}-{uuid.uuid4().hex[:8]}"

            JobRepository.create_job(
                session=session,
                job_id=child_job_id,
                job_type=JobType[step["agent"].upper()],
                request_payload=step.get("payload", {}),
                parent_job_id=job_id,
            )
            child_job_ids.append(child_job_id)

    # Update parent job with plan
    with get_db_session() as session:
        JobRepository.update_job_response(
            session=session,
            job_id=job_id,
            response_payload={
                "plan": plan,
                "child_jobs": child_job_ids,
            },
            status=JobStatus.COMPLETED,
        )

    return {
        "job_id": job_id,
        "plan": plan,
        "child_jobs": child_job_ids,
    }


# For local testing
if __name__ == "__main__":
    # Sample SQS event for testing
    test_event = {
        "Records": [
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "query": "Find 3BHK luxury apartments in Bangalore under 2 crore",
                    "user_id": "test-user-123",
                    "context": {
                        "budget": 20000000,
                        "city": "Bangalore",
                        "bedrooms": 3,
                    }
                })
            }
        ]
    }

    print("🧪 Testing Lambda handler locally...")
    result = lambda_handler(test_event, None)
    print(f"📊 Result: {json.dumps(result, indent=2)}")
