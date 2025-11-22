# Planner Agent

Creates execution plans using LLM and stores them in the database.

## Modes

- **Local**: FastAPI service (Tilt/Docker)
- **Production**: AWS Lambda (SQS trigger)

## Local Dev

```bash
tilt up  # Starts all services
curl http://localhost:8081/plan -H "Content-Type: application/json" -d '{"job_id":"test","query":"Find 3BHK in Noida"}'
```

## Files

```
src/main.py           - FastAPI app
src/lambda_handler.py - Lambda handler
src/planner.py        - LLM planning logic
```

## Env Variables

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=real_estate_agents
DB_USER=postgres
DB_PASSWORD=postgres
LLM_MODEL=bedrock/anthropic.claude-3-haiku-20240307-v1:0
```
