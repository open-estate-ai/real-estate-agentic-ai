# Database Module

PostgreSQL database for tracking agent jobs.

## Usage

```python
from database import JobRepository, JobStatus, JobType, get_db_session, init_db

# Create job
with get_db_session() as session:
    JobRepository.create_job(
        session=session,
        job_id="uuid-123",
        job_type=JobType.PLANNING,
        request_payload={"query": "Find 3BHK in Noida"},
    )

# Update status
with get_db_session() as session:
    JobRepository.update_job_status(
        session=session,
        job_id="uuid-123",
        status=JobStatus.COMPLETED,
    )
```

## Schema

See `migrations/001_init.sql` for full schema.

**Jobs table**: `job_id`, `type`, `status`, `request_payload`, `response_payload`, `parent_job_id`

## Local Dev

```bash
tilt up  # Starts PostgreSQL
```

Connection: `localhost:5432/real_estate_agents` (postgres/postgres)

## Env Variables

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=real_estate_agents
DB_USER=postgres
DB_PASSWORD=postgres
```
