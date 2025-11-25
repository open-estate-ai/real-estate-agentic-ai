locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.project_name))
}


# DB Subnet Group (using RDS Postgres Applicable VPC)
data "aws_vpc" "rds_vpc" {
  id = module.aurora_serverless_pg.vpc_id
}

# data "aws_subnets" "default" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.default.id]
#   }
# }
