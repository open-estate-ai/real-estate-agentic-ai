data "aws_caller_identity" "current" {}

# ========================================
# Aurora Serverless v2 PostgreSQL Cluster
# ========================================

# Random password for database
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# SSM Parameter Store for database credentials (SecureString)
resource "aws_ssm_parameter" "db_username" {
  name        = "/${var.env}/${local.resource_name_prefix_hyphenated}/db/username"
  description = "Database master username for Aurora cluster"
  type        = "String"
  value       = var.db_admin_username

  tags = {
    Name        = "${local.resource_name_prefix_hyphenated}-db-username"
    Environment = var.env
  }
}

resource "aws_ssm_parameter" "db_password" {
  name        = "/${var.env}/${local.resource_name_prefix_hyphenated}/db/password"
  description = "Database master password for Aurora cluster"
  type        = "SecureString"
  value       = random_password.db_password.result

  tags = {
    Name        = "${local.resource_name_prefix_hyphenated}-db-password"
    Environment = var.env
  }
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

resource "aws_db_subnet_group" "aurora" {
  name       = "${local.resource_name_prefix_hyphenated}-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
}

# Security group for Aurora
resource "aws_security_group" "aurora" {
  name        = "${local.resource_name_prefix_hyphenated}-sg"
  description = "Security group for Alex Aurora cluster"
  vpc_id      = data.aws_vpc.default.id

  # Allow PostgreSQL access from within VPC
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Aurora Serverless v2 Cluster
resource "aws_rds_cluster" "aurora" {
  cluster_identifier = "${local.resource_name_prefix_hyphenated}-cluster"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = "17.6"
  database_name      = var.db_name
  master_username    = var.db_admin_username
  master_password    = random_password.db_password.result

  # Serverless v2 scaling configuration
  serverlessv2_scaling_configuration {
    min_capacity = var.db_min_capacity
    max_capacity = var.db_max_capacity
  }

  # Enable Data API
  enable_http_endpoint = true

  # Enable IAM database authentication
  iam_database_authentication_enabled = true

  # Networking
  db_subnet_group_name   = aws_db_subnet_group.aurora.name
  vpc_security_group_ids = [aws_security_group.aurora.id]

  # Backup and maintenance
  backup_retention_period      = 7
  preferred_backup_window      = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"

  # Development settings
  skip_final_snapshot = true
  apply_immediately   = true
}

# Aurora Serverless v2 Instance
resource "aws_rds_cluster_instance" "aurora" {
  identifier         = "${local.resource_name_prefix_hyphenated}-aurora-instance-1"
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora.engine
  engine_version     = aws_rds_cluster.aurora.engine_version

  performance_insights_enabled = false # Save costs in development
}




# ========================================
# IAM Policy for Lambda Aurora Access
# ========================================
# This policy can be attached to any Lambda role that needs Aurora access

resource "aws_iam_policy" "lambda_aurora_access" {
  name        = "${local.resource_name_prefix_hyphenated}-lambda-aurora-access"
  description = "Policy for Lambda functions to access Aurora with IAM auth, Data API, and Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AuroraDataAPIAccess"
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = aws_rds_cluster.aurora.arn
      },
      {
        Sid    = "SSMParameterStoreAccess"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          aws_ssm_parameter.db_username.arn,
          aws_ssm_parameter.db_password.arn
        ]
      },
      {
        Sid    = "KMSDecryptForSSM"
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "ssm.${var.region}.amazonaws.com"
          }
        }
      },
      {
        Sid    = "RDSIAMAuthentication"
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = "arn:aws:rds-db:${var.region}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_rds_cluster.aurora.cluster_resource_id}/${var.db_admin_username}"
      }
    ]
  })
}
