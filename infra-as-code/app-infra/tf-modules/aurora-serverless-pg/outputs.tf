output "aurora_cluster_arn" {
  description = "ARN of the Aurora Serverless cluster"
  value       = aws_rds_cluster.aurora.arn
}

output "aurora_cluster_endpoint" {
  description = "Writer endpoint for the Aurora cluster"
  value       = aws_rds_cluster.aurora.endpoint
}

output "db_username_parameter_name" {
  description = "SSM Parameter Store name for database username"
  value       = aws_ssm_parameter.db_username.name
}

output "db_password_parameter_name" {
  description = "SSM Parameter Store name for database password (SecureString)"
  value       = aws_ssm_parameter.db_password.name
}

output "db_username_parameter_arn" {
  description = "ARN of SSM Parameter containing database username"
  value       = aws_ssm_parameter.db_username.arn
}

output "db_password_parameter_arn" {
  description = "ARN of SSM Parameter containing database password"
  value       = aws_ssm_parameter.db_password.arn
}

output "database_name" {
  description = "Name of the database"
  value       = aws_rds_cluster.aurora.database_name
}

output "data_api_enabled" {
  description = "Status of Data API"
  value       = aws_rds_cluster.aurora.enable_http_endpoint ? "Enabled" : "Disabled"
}

output "aurora_access_policy_arn" {
  description = "ARN of the IAM policy for Lambda functions to access Aurora (attach to Lambda role)"
  value       = aws_iam_policy.lambda_aurora_access.arn
}

output "database_port" {
  description = "Port of the Aurora cluster"
  value       = "5432"
}

output "master_username" {
  description = "Master database username"
  value       = var.db_admin_username
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions to access Aurora"
  value       = aws_security_group.lambda_aurora_access.id
}

output "aurora_security_group_id" {
  description = "Security group ID for Aurora cluster"
  value       = aws_security_group.aurora.id
}
