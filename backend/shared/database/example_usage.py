"""
Example usage of the shared database module.

Run this script to test database connectivity and operations.
"""

import uuid
from datetime import datetime, timezone

from database import (
    JobRepository,
    JobStatus,
    JobType,
    get_db_session,
    init_db,
)


def main():
    """Test database operations."""

    # Initialize database (create tables)
    print("Initializing database...")
    init_db()
    print("✅ Database initialized\n")

    # Create a job
    job_id = str(uuid.uuid4())
    print(f"Creating job with ID: {job_id}")

    with get_db_session() as session:
        job = JobRepository.create_job(
            session=session,
            job_id=job_id,
            job_type=JobType.PLANNING,
            request_payload={
                "query": "Find 3BHK apartments in Noida under 1CR",
                "user_id": "user-123",
            },
        )
        print(f"✅ Job created: {job.to_dict()}\n")

    # Update job status to in_progress
    print(f"Updating job {job_id} to IN_PROGRESS...")
    with get_db_session() as session:
        job = JobRepository.update_job_status(
            session=session,
            job_id=job_id,
            status=JobStatus.IN_PROGRESS,
        )
        print(f"✅ Job updated: status={job.status}\n")

    # Simulate some processing time
    print("Processing...")

    # Update job with results
    print(f"Storing results for job {job_id}...")
    with get_db_session() as session:
        job = JobRepository.update_job_response(
            session=session,
            job_id=job_id,
            response_payload={
                "plan": {
                    "steps": [
                        {"agent": "search", "action": "find_listings"},
                        {"agent": "valuation", "action": "estimate_price"},
                        {"agent": "summarizer", "action": "generate_report"},
                    ]
                },
                "estimated_duration_seconds": 45,
            },
            status=JobStatus.COMPLETED,
        )
        print(f"✅ Job completed: {job.to_dict()}\n")

    # Create child jobs
    print("Creating child jobs for multi-step workflow...")
    child_job_ids = []

    with get_db_session() as session:
        # Search job
        search_job_id = str(uuid.uuid4())
        search_job = JobRepository.create_job(
            session=session,
            job_id=search_job_id,
            job_type=JobType.SEARCH,
            request_payload={"query": "3BHK Noida", "max_results": 50},
            parent_job_id=job_id,
        )
        child_job_ids.append(search_job_id)
        print(f"  ✅ Created search job: {search_job_id}")

        # Valuation job
        valuation_job_id = str(uuid.uuid4())
        valuation_job = JobRepository.create_job(
            session=session,
            job_id=valuation_job_id,
            job_type=JobType.VALUATION,
            request_payload={"listing_ids": ["l1", "l2", "l3"]},
            parent_job_id=job_id,
        )
        child_job_ids.append(valuation_job_id)
        print(f"  ✅ Created valuation job: {valuation_job_id}")

    print()

    # Query child jobs
    print(f"Querying child jobs for parent {job_id}...")
    with get_db_session() as session:
        children = JobRepository.get_child_jobs(
            session=session,
            parent_job_id=job_id,
        )
        print(f"✅ Found {len(children)} child jobs:")
        for child in children:
            print(
                f"  - {child.job_id}: type={child.type}, status={child.status}")

    print()

    # Query jobs by status
    print("Querying all pending jobs...")
    with get_db_session() as session:
        pending_jobs = JobRepository.get_jobs_by_status(
            session=session,
            status=JobStatus.PENDING,
            limit=10,
        )
        print(f"✅ Found {len(pending_jobs)} pending jobs:")
        for pending_job in pending_jobs:
            print(f"  - {pending_job.job_id}: type={pending_job.type}")

    print()

    # Query jobs by type
    print("Querying all planning jobs...")
    with get_db_session() as session:
        planning_jobs = JobRepository.get_jobs_by_type(
            session=session,
            job_type=JobType.PLANNING,
            limit=10,
        )
        print(f"✅ Found {len(planning_jobs)} planning jobs:")
        for planning_job in planning_jobs:
            print(f"  - {planning_job.job_id}: status={planning_job.status}")

    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    main()
