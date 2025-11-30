resource "aws_iam_policy" "sqs_access_policy_from_producer_lambdas" {
  name        = "${local.resource_name_prefix_hyphenated}-sqs-access-policy-from-producer-lambdas"
  description = "Policy for Lambda functions to send messages to SQS queues"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSQueueSendMessage"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.analysis_jobs.arn
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "sqs_access_policy_from_consumer_lambdas" {
  name        = "${local.resource_name_prefix_hyphenated}-sqs-access-policy-from-consumer-lambdas"
  description = "Policy for Lambda functions to access SQS queues"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSQueueAccess"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.analysis_jobs.arn,
          aws_sqs_queue.analysis_jobs_dlq.arn
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "s3_vector_access_policy" {
  name        = "${local.resource_name_prefix_hyphenated}-s3-vector-access-policy"
  description = "Policy for Lambda functions to access S3 Vectors"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3VectorAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_vector_bucket_name}",
          "arn:aws:s3:::${var.s3_vector_bucket_name}/*"
        ]
      },
      {
        Sid    = "S3VectorAPIAccess"
        Effect = "Allow"
        Action = [
          "s3vectors:QueryVectors",
          "s3vectors:GetVectors"
        ]
        Resource = [
          "arn:aws:s3vectors:${var.resource_region}:${data.aws_caller_identity.current.account_id}:bucket/${var.s3_vector_bucket_name}/index/*",
        ]
      }


    ]
  })
}

resource "aws_iam_policy" "invoke_all_agents_lambda_invoke_policy" {
  name        = "${local.resource_name_prefix_hyphenated}-invoke-all-agents-lambda-policy"
  description = "Policy for Lambda functions to invoke all other agent Lambdas"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeAllAgentsLambdas"
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.resource_region}:${data.aws_caller_identity.current.account_id}:function:${local.resource_name_prefix_hyphenated}-*"
      }
    ]
  })
  
}

resource "aws_iam_policy" "lambda_sagemaker_access_policy" {
  name        = "${local.resource_name_prefix_hyphenated}-lambda-sagemaker-access-policy"
  description = "Policy for Lambda functions to access SageMaker Endpoints"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SageMakerEndpointAccess"
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = "arn:aws:sagemaker:${var.resource_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.sagemaker_endpoint}"
      }
    ]
  })
  
}

resource "aws_iam_policy" "bedrock_invoke_policy" {
  name        = "${local.resource_name_prefix_hyphenated}-bedrock-invoke-policy"
  description = "Policy for Lambda functions to invoke Bedrock models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockModelInvoke"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels"
        ]
        Resource = [
          "arn:aws:bedrock:${var.bedrock_region}::foundation-model/*",
          "arn:aws:bedrock:${var.bedrock_region}:*:inference-profile/*"
        ]
      }
    ]
  })
  
}   