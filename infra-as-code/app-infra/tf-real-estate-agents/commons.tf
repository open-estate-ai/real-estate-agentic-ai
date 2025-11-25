locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.project_name))
}


# DB Subnet Group (using default VPC)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
