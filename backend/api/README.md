# Backend API

The entry point for the real estate AI system. Receives user queries, invokes the Planner Agent, and provides endpoints to query job status and results from the database.

## What It Does

- Receives user queries via `/api/analyze` endpoint
- Routes requests to Planner Agent (HTTP locally, SQS in production)
- Provides job status and results via `/api/jobs/{job_id}`
- Health check endpoint with database connectivity validation
- Retrieves job details and output from the database

## Data Payload Structure

### **Request Format**

All requests to `/api/analyze` should use this simplified structure:

```json
{
  "user_id": "user-123",
  "request_payload": {
    "user_query": "Find 3BHK apartments in Noida under 1 crore"
  }
}
```

**Fields:**
- `user_id` *(string, optional)*: User identifier for tracking and personalization
- `request_payload` *(object, required)*: Container for query data
  - `user_query` *(string, required)*: User's natural language query

### **Response Format**

Successful analysis request returns:

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Query submitted for analysis"
}
```

**Fields:**
- `job_id` *(string)*: UUID for tracking job status and results
- `message` *(string)*: Confirmation message

### **Sample Queries**

```json
// Real estate search
{
  "user_id": "user-456",
  "request_payload": {
    "user_query": "Show me 2BHK apartments in Gurgaon with parking under 80 lakhs"
  }
}

// Property valuation
{
  "user_id": "user-789",
  "request_payload": {
    "user_query": "What's the market value of a 3BHK apartment in Sector 62 Noida"
  }
}

// Investment analysis
{
  "user_id": "user-101",
  "request_payload": {
    "user_query": "Compare rental yields between Noida and Gurgaon for 2BHK flats"
  }
}
```

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
    "user_id": "user-123",
    "request_payload": {
      "user_query": "Find 3BHK apartments in Noida under 1 crore"
    }
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
    "body": "{\"user_id\":\"user-123\",\"request_payload\":{\"user_query\":\"Find 3BHK apartments in Noida under 1 crore\"}}",
    "isBase64Encoded": false
  }'
```

## Test AWS Lambda (Post-Deployment)

### Prerequisites

- AWS CLI configured
- Lambda function deployed
- `jq` installed for JSON parsing

### Set Environment Variables

```bash
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="756375699536"
export ENVIRONMENT="dev"
export LAMBDA_FUNCTION_NAME="${ENVIRONMENT}-open-estate-ai-backend-api"
export LAMBDA_FUNCTION_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_FUNCTION_NAME}"
```


### Quick Health Check

```bash
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_ARN" \
  --payload "{\"version\":\"2.0\",\"routeKey\":\"GET /api/\",\"rawPath\":\"/api/\",\"headers\":{\"accept\":\"application/json\"},\"requestContext\":{\"accountId\":\"${AWS_ACCOUNT_ID}\",\"apiId\":\"test\",\"domainName\":\"test.execute-api.${AWS_REGION}.amazonaws.com\",\"domainPrefix\":\"test\",\"http\":{\"method\":\"GET\",\"path\":\"/api/\",\"protocol\":\"HTTP/1.1\",\"sourceIp\":\"127.0.0.1\",\"userAgent\":\"aws-cli\"},\"requestId\":\"test\",\"routeKey\":\"GET /api/\",\"stage\":\"\$default\",\"time\":\"23/Nov/2025:10:00:00 +0000\",\"timeEpoch\":1700740800000},\"isBase64Encoded\":false}" \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-response.json && cat /tmp/lambda-response.json | jq '.'
```

### Health Check with Database Status

```bash
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_ARN" \
  --payload "{\"version\":\"2.0\",\"routeKey\":\"GET /api/health\",\"rawPath\":\"/api/health\",\"headers\":{\"accept\":\"application/json\"},\"requestContext\":{\"accountId\":\"${AWS_ACCOUNT_ID}\",\"http\":{\"method\":\"GET\",\"path\":\"/api/health\",\"sourceIp\":\"127.0.0.1\"}},\"isBase64Encoded\":false}" \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-response.json && cat /tmp/lambda-response.json | jq '.'
```

### Analyze Query

```bash
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_ARN" \
  --payload '{"version":"2.0","routeKey":"POST /api/analyze","rawPath":"/api/analyze","headers":{"content-type":"application/json"},"requestContext":{"accountId":"'${AWS_ACCOUNT_ID}'","http":{"method":"POST","path":"/api/analyze","sourceIp":"127.0.0.1"}},"body":"{\"user_id\":\"user-123\",\"request_payload\":{\"user_query\":\"Find 3BHK apartments in Noida under 1 crore\"}}","isBase64Encoded":false}' \
  /tmp/lambda-response.json && cat /tmp/lambda-response.json | jq '.'
```

### Get Job Status

```bash
# Set job_id from analyze response
export JOB_ID="job-abc12345"

aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_ARN" \
  --payload "{\"version\":\"2.0\",\"routeKey\":\"GET /api/jobs/{job_id}\",\"rawPath\":\"/api/jobs/${JOB_ID}\",\"pathParameters\":{\"job_id\":\"${JOB_ID}\"},\"headers\":{\"accept\":\"application/json\"},\"requestContext\":{\"accountId\":\"${AWS_ACCOUNT_ID}\",\"http\":{\"method\":\"GET\",\"path\":\"/api/jobs/${JOB_ID}\",\"sourceIp\":\"127.0.0.1\"}},\"isBase64Encoded\":false}" \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-response.json && cat /tmp/lambda-response.json | jq '.'
```

### View Lambda Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/${LAMBDA_FUNCTION_NAME} --follow

# Get recent logs (last 10 minutes)
aws logs tail /aws/lambda/${LAMBDA_FUNCTION_NAME} --since 10m --format short
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
