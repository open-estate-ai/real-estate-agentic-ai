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
