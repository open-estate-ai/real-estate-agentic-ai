# Backend

Multi-agent system for real estate AI.

## Local Development

```bash
# From repo root
cd real-estate-agentic-ai
tilt up
```

### Test Planner Agent API

```bash
# Health check
curl http://localhost:8080/health

# Create a plan
curl -X POST http://localhost:8080/plan \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-'$(date +%s)'",
    "query": "Find 3BHK apartments in Noida under 1 crore with parking",
    "user_id": "test-user-123"
  }'

# Get job status
curl http://localhost:8080/jobs/<job_id>

# Get child jobs
curl http://localhost:8080/jobs/<job_id>/children
```

## Docker Builds

### Planner Agent (Local/Dev)

```bash
cd backend
docker build -f agents/planner/Dockerfile -t planner-agent --target localdev .
```

### Planner Agent (Lambda)

```bash
cd backend
docker build -f agents/planner/Dockerfile.lambda -t planner-agent-lambda .
```

## Test Lambda Locally

```bash
cd backend

# Stop any existing container on port 9000
docker ps | grep 9000 && docker stop $(docker ps -q --filter "publish=9000")

# Run Lambda container locally
docker run --rm -p 9000:8080 \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PORT=5432 \
  -e DATABASE_NAME=real_estate_agents \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=postgres \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  -e LLM_MODEL=bedrock/anthropic.claude-3-haiku-20240307-v1:0 \
  planner-agent-lambda

# Invoke Lambda (in another terminal)
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "Records": [{
      "messageId": "test-'$(date +%s)'",
      "body": "{\"query\":\"Find 3BHK apartments in Noida\",\"user_id\":\"test-user\"}"
    }]
  }'

# Note: Use unique messageId for each test (timestamp added above)
```

## Lambda Deployment

### 1. Build and Push to ECR

```bash
cd backend

# Build Lambda image
docker build -f agents/planner/Dockerfile.lambda -t planner-agent-lambda .

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository (first time only)
aws ecr create-repository --repository-name planner-agent-lambda --region us-east-1

# Tag and push
docker tag planner-agent-lambda:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/planner-agent-lambda:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/planner-agent-lambda:latest
```

### 2. Create Lambda Function

```bash
aws lambda create-function \
  --function-name planner-agent \
  --package-type Image \
  --code ImageUri=<account-id>.dkr.ecr.us-east-1.amazonaws.com/planner-agent-lambda:latest \
  --role arn:aws:iam::<account-id>:role/lambda-execution-role \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{DB_HOST=<rds-endpoint>,DB_NAME=real_estate_agents,LLM_MODEL=bedrock/anthropic.claude-3-haiku-20240307-v1:0}" \
  --region us-east-1
```

### 3. Update Lambda Function

```bash
# Rebuild and push new image
docker build -f agents/planner/Dockerfile.lambda -t planner-agent-lambda .
docker tag planner-agent-lambda:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/planner-agent-lambda:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/planner-agent-lambda:latest

# Update Lambda to use new image
aws lambda update-function-code \
  --function-name planner-agent \
  --image-uri <account-id>.dkr.ecr.us-east-1.amazonaws.com/planner-agent-lambda:latest \
  --region us-east-1
```

### 4. Configure SQS Trigger

```bash
# Create SQS queue
aws sqs create-queue --queue-name agent-jobs-planning --region us-east-1

# Add SQS as event source
aws lambda create-event-source-mapping \
  --function-name planner-agent \
  --event-source-arn arn:aws:sqs:us-east-1:<account-id>:agent-jobs-planning \
  --batch-size 1 \
  --region us-east-1
```

### 5. Test Lambda

```bash
# Send test message to SQS
aws sqs send-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/<account-id>/agent-jobs-planning \
  --message-body '{"query":"Find 3BHK apartments in Noida","user_id":"test-user"}' \
  --region us-east-1

# Check Lambda logs
aws logs tail /aws/lambda/planner-agent --follow
```

## Structure

```
backend/
├── shared/          - Shared modules (database, etc.)
└── agents/
    └── planner/     - Planning agent
```
