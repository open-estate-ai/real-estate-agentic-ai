variable "backend_directory" {
  type        = string
  description = "Path to the backend directory for Terraform state"
  default     = "../../../../backend"
}
# Folder that contains Dockerfile + Lambda source
variable "lambda_src_dir" {
  type        = string
  description = "Path to the folder containing Dockerfile and Lambda code"
}

variable "lambda_name" {
  type = string
}

variable "lambda_memory_size" {
  type        = number
  description = "Lambda memory in MB"
  default     = 512
}

variable "lambda_timeout" {
  type        = number
  description = "Lambda timeout in seconds"
  default     = 30
}

variable "environment_variables" {
  type        = map(string)
  description = "Environment variables to pass to the Lambda function"
  default     = {}
}

variable "additional_iam_policy_arns" {
  type        = list(string)
  description = "Optional: Additional IAM policy ARNs to attach to Lambda role (e.g., Aurora access policy)"
  default     = []
}

variable "vpc_subnet_ids" {
  type        = list(string)
  description = "Optional: VPC subnet IDs for Lambda function"
  default     = []
}

variable "vpc_security_group_ids" {
  type        = list(string)
  description = "Optional: VPC security group IDs for Lambda function"
  default     = []
}
