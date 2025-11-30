# ========================================
# SQS Queue for Async Job Processing
# ========================================

resource "aws_sqs_queue" "analysis_jobs" {
  name                       = "${local.resource_name_prefix_hyphenated}-analysis-jobs-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400  # 1 day
  receive_wait_time_seconds = 10     # Long polling
  visibility_timeout_seconds = 910   # 15 minutes + 10 seconds buffer (matches Planner Lambda timeout)
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.analysis_jobs_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "analysis_jobs_dlq" {
  name = "${local.resource_name_prefix_hyphenated}-analysis-jobs-dlq"
}