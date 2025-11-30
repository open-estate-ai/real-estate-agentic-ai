# ========================================
# VPC Endpoints for Lambda to access AWS Services
# ========================================
# Lambda in VPC needs VPC endpoints to reach AWS services without NAT Gateway

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = "${local.resource_name_prefix_hyphenated}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = data.aws_vpc.default.id

  # Allow HTTPS from Lambda security group
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [module.aurora_serverless_pg.lambda_security_group_id]
    description     = "Allow HTTPS from Lambda"
  }

  # Allow HTTPS from VPC CIDR
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
    description = "Allow HTTPS from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

# VPC Endpoint for SSM (required for Parameter Store)
resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

# VPC Endpoint for SSM Messages (required for Session Manager if needed)
resource "aws_vpc_endpoint" "ssmmessages" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.ssmmessages"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

}

# VPC Endpoint for KMS (required for decrypting SecureString parameters)
resource "aws_vpc_endpoint" "kms" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.kms"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

# VPC Endpoint for SQS (required for Lambda to access SQS queues)
resource "aws_vpc_endpoint" "sqs" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "lambda" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.lambda"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "bedrock" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.bedrock"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "bedrock-runtime" {
  vpc_id              = data.aws_vpc.default.id
  service_name        = "com.amazonaws.${var.resource_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.default.ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}