# Output values for the Real Estate Agents infrastructure

output "aurora_cluster_endpoint" {
  description = "Aurora cluster endpoint"
  value       = module.aurora_serverless_pg.aurora_cluster_endpoint
}

output "database_name" {
  description = "Database name"
  value       = module.aurora_serverless_pg.database_name
}

output "database_port" {
  description = "Database port"
  value       = module.aurora_serverless_pg.database_port
}

output "master_username" {
  description = "Master database username"
  value       = module.aurora_serverless_pg.master_username
}

output "lambda_function_arn" {
  description = "Backend API Lambda function ARN"
  value       = module.tf_lambda_backend_api.lambda_function_arn
}
