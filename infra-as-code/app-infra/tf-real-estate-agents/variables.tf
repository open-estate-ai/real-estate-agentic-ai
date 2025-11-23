variable "project_name" {
  type = string
}

variable "log_level" {
  type        = string
  description = "Application log level"
  default     = "INFO"
}

# RDS Serverless Configuration
variable "database_host" {
  type        = string
  description = "RDS Serverless cluster endpoint"
  default     = ""
}

variable "database_port" {
  type        = string
  description = "Database port"
  default     = "5432"
}

variable "database_name" {
  type        = string
  description = "Database name"
  default     = "real_estate_agents"
}

variable "database_user" {
  type        = string
  description = "Database username (IAM-enabled user for RDS Serverless)"
  default     = ""
}

variable "aws_region" {
  type        = string
  description = "AWS region for RDS IAM authentication"
  default     = "us-east-1"
}

variable "planner_agent_url" {
  type        = string
  description = "Planner Agent HTTP endpoint URL"
  default     = ""
}
