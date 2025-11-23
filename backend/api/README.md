# Backend API

The entry point for the real estate AI system. Receives user queries, invokes the Planner Agent, and provides endpoints to query job status and results from the database.

## What It Does

- Receives user queries via `/api/analyze` endpoint
- Routes requests to Planner Agent (HTTP locally, SQS in production)
- Provides job status and results via `/api/jobs/{job_id}`
- Health check endpoint with database connectivity validation
- Retrieves job details and output from the database

## Local Development

### Run with Tilt

```bash
cd real-estate-agentic-ai
tilt up
```

### Test Locally

**Submit a Query:**
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find 3BHK apartments in Noida under 1 crore",
    "user_id": "user-123"
  }'
```

**Check Job Status:**
```bash
curl http://localhost:8080/api/jobs/{job_id}
```

**Health Check:**
```bash
curl http://localhost:8080/api/health
```

## Run as AWS Lambda Locally

### Build Lambda Image

```bash
cd backend
docker build -f api/Dockerfile.lambda -t backend-api-lambda .
```

### Run Lambda Container (Locally)

Ensure PostgreSQL 17.6 is running locally before starting the Lambda container.

```bash
# Stop any existing container on port 9001
docker ps | grep 9001 && docker stop $(docker ps -q --filter "publish=9001")

# Run Lambda container
docker run --rm -p 9001:8080 \
  -e ENV=local \
  -e PLANNER_AGENT_URL=http://host.docker.internal:8081 \
  -e LOG_LEVEL=DEBUG \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PORT=5432 \
  -e DATABASE_NAME=real_estate_agents \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=postgres \
  backend-api-lambda
```

### Test Lambda Locally

**Simulate API Gateway Event:**
```bash
curl -X POST "http://localhost:9001/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "routeKey": "POST /api/analyze",
    "rawPath": "/api/analyze",
    "rawQueryString": "",
    "headers": {
      "content-type": "application/json"
    },
    "requestContext": {
      "accountId": "123456789012",
      "apiId": "test-api-id",
      "domainName": "test.execute-api.us-east-1.amazonaws.com",
      "domainPrefix": "test",
      "http": {
        "method": "POST",
        "path": "/api/analyze",
        "protocol": "HTTP/1.1",
        "sourceIp": "127.0.0.1",
        "userAgent": "curl/7.64.1"
      },
      "requestId": "test-request-id",
      "routeKey": "POST /api/analyze",
      "stage": "$default",
      "time": "09/Nov/2023:12:34:56 +0000",
      "timeEpoch": 1699534496000
    },
    "body": "{\"query\":\"Find 3BHK apartments in Noida under 1 crore\",\"user_id\":\"user-123\"}",
    "isBase64Encoded": false
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | Database hostname | `localhost` |
| `DATABASE_PORT` | Database port | `5432` |
| `DATABASE_NAME` | Database name | `real_estate_agents` |
| `DATABASE_USER` | Database username | `postgres` |
| `DATABASE_PASSWORD` | Database password | `postgres` |
| `ENV` | Environment (local/production) | `local` |
| `PLANNER_AGENT_URL` | Planner Agent HTTP endpoint | `http://localhost:8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Architecture

```
User Request → Backend API → Planner Agent → Database
                    ↓              ↓
                Database ← LLM (Bedrock)
```

**Flow:**
1. User submits query to `/api/analyze`
2. Backend API creates initial job entry in database
3. Routes request to Planner Agent (HTTP locally, SQS in production)
4. Planner Agent processes with LLM and stores execution plan
5. User queries `/api/jobs/{job_id}` for status and results
6. Backend API retrieves job details from database

## Files

- `src/local_api.py` - FastAPI application with endpoints
- `src/lambda_handler.py` - AWS Lambda handler (API Gateway events)
- `src/clients/planner_client.py` - HTTP client for Planner Agent communication
- `src/services/api_service.py` - Business logic layer
- `Dockerfile` - Local development image (Tilt)
- `Dockerfile.lambda` - AWS Lambda deployment image
