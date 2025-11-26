variable "vpc_id" {
  type = string
}
variable "vpc_cidr_block" {
  type = string
}

variable "vpc_subnet_ids" {
  type = list(string)
}

variable "db_admin_username" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_min_capacity" {
  description = "Minimum capacity for Aurora Serverless v2 (in ACUs)"
  type        = number
  default     = 0.5
}

variable "db_max_capacity" {
  description = "Maximum capacity for Aurora Serverless v2 (in ACUs)"
  type        = number
  default     = 1
}
