# Backend

The backend service for our real estate AI system.

## What's Inside

- **API Service** - Receives user queries and coordinates the work
- **Agents** - Specialized services that handle different tasks (planning, legal checks, etc.)
- **Shared** - Common code used by all services

## Running Locally

Start all services:

```bash
cd real-estate-agentic-ai
tilt up
```

This runs:
- Backend API (port 8080)
- Planner Agent (port 8081)
- PostgreSQL database


## How It Works

When deployed to AWS:

1. User sends request → API Gateway
2. Backend Lambda processes it → sends to SQS queue
3. Planner Agent Lambda picks up the job
4. Planner coordinates other agents as needed
5. Results saved to database

### AWS Services Used

- **API Gateway** - HTTP endpoints
- **Lambda** - Runs our code
- **SQS** - Message queue
- **Aurora PostgreSQL** - Database
- **Bedrock (Claude)** - AI capabilities
- **SageMaker** - Embeddings
- **S3** - Vector storage

The architecture diagram above shows how everything connects.

## Components

### API Service

The entry point. Receives user queries and queues them for processing.

See [api/README.md](api/README.md) for more details.

### Planner Agent

Reads from the queue, analyzes queries, and coordinates other agents.

See [agents/planner/README.md](agents/planner/README.md) for more details.

### Shared Code

Common modules for database access, models, and utilities. Located in `shared/`.

## Testing Locally

Test the system:

```bash
# Submit a query
curl -X POST http://localhost:9000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find 3BHK apartments in Noida under 1 crore",
    "user_id": "user-123"
  }'

# Check status (use job_id from response)
curl http://localhost:9000/api/jobs/{job_id}
```

## Testing in AWS

After deploying, test via API Gateway:

### Set API Gateway URL

```bash
export API_GATEWAY_URL="https://<api-gateway-id>.execute-api.us-east-1.amazonaws.com"
```

### Submit Analysis Request

```bash
curl -X POST ${API_GATEWAY_URL}/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "request_payload": {
      "user_query": "Find 3BHK apartments in Noida under 1 crore"
    }
  }'
```

**Expected Response:**
```json
{
  "job_id": "b0537f4e-7a27-47b6-bc7a-5310ac2de943",
  "message": "Query submitted for analysis",
  "sqs_message_id": "abc123..."
}
```

### Get Job Status

```bash
# Replace with actual job_id from analyze response
export JOB_ID="b0537f4e-7a27-47b6-bc7a-5310ac2de943"

curl -X GET "${API_GATEWAY_URL}/api/jobs/${JOB_ID}" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "job_id": "b0537f4e-7a27-47b6-bc7a-5310ac2de943",
  "type": "planning",
  "status": "completed",
  "request_payload": {
    "user_query": "Find 3BHK apartments in Noida under 1 crore"
  },
  "output": {
    "plan": "..."
  }
}
```

### Health Check

```bash
curl -X GET "${API_GATEWAY_URL}/api/health" \
  -H "accept: application/json"
```

## Project Structure

```
backend/
├── api/                    # Backend API service
│   ├── src/
│   │   ├── main.py        # FastAPI app
│   │   ├── lambda_handler.py
│   │   ├── clients/       # HTTP clients
│   │   └── services/      # Business logic
│   ├── Dockerfile
│   ├── Dockerfile.lambda
│   └── README.md
├── agents/
│   └── planner/           # Planner agent
│       ├── src/
│       │   ├── main.py    # FastAPI app
│       │   ├── lambda_handler.py
│       │   ├── planner.py # LLM logic
│       │   └── services/  # Business logic
│       ├── Dockerfile
│       ├── Dockerfile.lambda
│       └── README.md
└── shared/                # Shared modules
    ├── __init__.py
    ├── database/
    │   ├── models.py      # SQLAlchemy models
    │   ├── repository.py  # Data access layer
    │   └── session.py     # DB connection
    └── pyproject.toml
```
