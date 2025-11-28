# Planner Agent

The first agent in the pipeline. Receives user queries from SQS, analyzes them using LLM, and creates execution plans stored in the database.

## What It Does

- Reads messages from SQS queue (production) or HTTP requests (local)
- Uses LLM to break down user queries into actionable steps
- Creates a planning job and stores the execution plan in the database
- Returns job_id for tracking progress

## Local Development

### Run with Tilt

```bash
cd real-estate-agentic-ai
tilt up
```

### Test Locally

```bash
curl -X POST http://localhost:8081/user-query \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-123",
    "user_id": "user-123",
    "request_payload": {
      "user_query": "Find 3BHK apartments in Noida under 1 crore"
    }
  }'
```

## Run as AWS Lambda Locally

### Build Lambda Image

```bash
cd backend
docker build -f agents/planner/Dockerfile.lambda -t planner-agent-lambda .
```

### Run Lambda Container (Locally)

Ensure PostgreSQL 17.6 is running locally before starting the Lambda container.

```bash
# Stop any existing container on port 9081
docker ps | grep 9081 && docker stop $(docker ps -q --filter "publish=9081")

# Run Lambda container
docker run --rm -p 9081:8080 \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PORT=5432 \
  -e DATABASE_NAME=real_estate_agents \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=postgres \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  -e LLM_MODEL=bedrock/openai.gpt-oss-120b-1:0\
  planner-agent-lambda
```

### Test Lambda Locally

Simulate SQS message:
```bash
curl -X POST "http://localhost:9081/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "Records": [{
      "messageId": "test-msg-123",
      "body": "{\"user_id\":\"user-123\",\"request_payload\":{\"user_query\":\"Find 3BHK apartments in Noida\"}}"
    }]
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
export LAMBDA_FUNCTION_NAME="${ENVIRONMENT}-open-estate-ai-planner-agent"
export LAMBDA_FUNCTION_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_FUNCTION_NAME}"
export TEST_MESSAGE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
```

### Analyze Query

```bash
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_ARN" \
  --payload '{
    "Records": [
      {
        "messageId": "1234",
        "receiptHandle": "test-receipt-handle",
        "body": "{\"user_id\":\"user-123\",\"request_payload\":{\"user_query\":\"Find 3BHK apartments in Noida under 1 crore\"}}",
        "attributes": {
          "ApproximateReceiveCount": "1",
          "SentTimestamp": "1700000000000",
          "SenderId": "AIDAIT2UOQQY3AUEKVGXU",
          "ApproximateFirstReceiveTimestamp": "1700000000000"
        },
        "messageAttributes": {},
        "md5OfBody": "test-md5",
        "eventSource": "aws:sqs",
        "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:test-queue",
        "awsRegion": "us-east-1"
      }
    ]
  }' \
  --cli-binary-format raw-in-base64-out \
  /tmp/planner-response.json && cat /tmp/planner-response.json | jq '.'
```


### View Lambda Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/${LAMBDA_FUNCTION_NAME} --follow

# Get recent logs (last 10 minutes)
aws logs tail /aws/lambda/${LAMBDA_FUNCTION_NAME} --since 10m --format short



## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | Database hostname | `localhost` |
| `DATABASE_PORT` | Database port | `5432` |
| `DATABASE_NAME` | Database name | `real_estate_agents` |
| `DATABASE_USER` | Database username | `postgres` |
| `DATABASE_PASSWORD` | Database password | `postgres` |
| `AWS_ACCESS_KEY_ID` | AWS credentials for Bedrock | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for Bedrock | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `LLM_MODEL` | LLM model identifier | `bedrock/openai.gpt-oss-120b-1:0` |

## Architecture

```
SQS Queue → Lambda Handler → Planner Service → Database
                    ↓
                  LLM (Bedrock)
```

**Flow:**
1. Message arrives in SQS queue
2. Lambda handler extracts query and user_id
3. Planner service creates a planning job
4. LLM analyzes query and generates execution plan
5. Plan stored in database with job_id
6. Response returned with job details

## Files

- `src/main.py` - FastAPI application (local development)
- `src/lambda_handler.py` - AWS Lambda handler (SQS events)
- `src/planner.py` - Core LLM planning logic
- `src/services/planner_service.py` - Business logic layer
- `Dockerfile` - Local development image (Tilt)
- `Dockerfile.lambda` - AWS Lambda deployment image
