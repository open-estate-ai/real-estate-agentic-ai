
module "aurora_serverless_pg" {
  source            = "../tf-modules/aurora-serverless-pg"
  env               = var.env
  region            = var.resource_region
  project_name      = var.project_name
  vpc_id         = data.aws_vpc.default.id
  vpc_cidr_block = data.aws_vpc.default.cidr_block
  vpc_subnet_ids = data.aws_subnets.default.ids
  db_admin_username = "adminuser"
  db_name           = "real_estate_agents"  
}


#########################################################################################
################################################################
# Backend API Lambda Function
###########################################################################################
#########################################################################################

module "tf_lambda_backend_api" {
  source         = "../tf-modules/tf-lambda"
  env            = var.env
  region         = var.resource_region
  lambda_name    = "${var.project_name}-backend-api"
  lambda_src_dir = "api"

  # Attach Aurora access policy to Lambda's own role
  additional_iam_policy_arns = [
    module.aurora_serverless_pg.aurora_access_policy_arn,
    aws_iam_policy.sqs_access_policy_from_producer_lambdas.arn,
  ]

  # VPC configuration to access Aurora in private subnets
  vpc_subnet_ids         = data.aws_subnets.default.ids
  vpc_security_group_ids = [
    module.aurora_serverless_pg.lambda_security_group_id,
  ]

  environment_variables = merge(
    {
      ENV       = var.env
      LOG_LEVEL = var.log_level
    },
    # Database configuration from Aurora Serverless module outputs
    {
      DATABASE_HOST   = module.aurora_serverless_pg.aurora_cluster_endpoint
      DATABASE_PORT   = module.aurora_serverless_pg.database_port
      DATABASE_NAME   = module.aurora_serverless_pg.database_name
      DB_POOL_SIZE    = "2"
      DB_POOL_RECYCLE = "3600"
      # SSM Parameter Store paths for credentials
      DB_USERNAME_SSM_PARAM = module.aurora_serverless_pg.db_username_parameter_name
      DB_PASSWORD_SSM_PARAM = module.aurora_serverless_pg.db_password_parameter_name

      # SQS QUEUE URL for analysis jobs
      SQS_QUEUE_URL = aws_sqs_queue.analysis_jobs.url

    },
    # Only add planner agent URL if configured
    var.planner_agent_url != "" ? {
      PLANNER_AGENT_URL = var.planner_agent_url
    } : {}
  )
}

########################################################################################
#######################################################################
# Planner Agent Lambda Function
###############################################################################################
########################################################################################


# SQS trigger for Planner
resource "aws_lambda_event_source_mapping" "planner_sqs" {
  event_source_arn = aws_sqs_queue.analysis_jobs.arn
  function_name    = module.tf_lambda_planner_agent.lambda_function_arn
  batch_size       = 1
}

module "tf_lambda_planner_agent" {
  source         = "../tf-modules/tf-lambda"
  env            = var.env
  region         = var.resource_region
  lambda_name    = "${var.project_name}-planner-agent"
  lambda_src_dir = "agents/planner"
  lambda_timeout = 300  # 5 minutes for LLM operations and agent invocations

  # Attach Aurora access policy to Lambda's own role
  additional_iam_policy_arns = [
    module.aurora_serverless_pg.aurora_access_policy_arn,
    aws_iam_policy.sqs_access_policy_from_consumer_lambdas.arn,
    aws_iam_policy.s3_vector_access_policy.arn,
    aws_iam_policy.invoke_all_agents_lambda_invoke_policy.arn,
    aws_iam_policy.lambda_sagemaker_access_policy.arn,
    aws_iam_policy.bedrock_invoke_policy.arn,
  ]

  # VPC configuration to access Aurora in private subnets
  vpc_subnet_ids         = data.aws_subnets.default.ids
  vpc_security_group_ids = [module.aurora_serverless_pg.lambda_security_group_id]

  environment_variables = merge(
    {
      ENV       = var.env
      LOG_LEVEL = var.log_level
    },
    # Database configuration from Aurora Serverless module outputs
    {
      DATABASE_HOST   = module.aurora_serverless_pg.aurora_cluster_endpoint
      DATABASE_PORT   = module.aurora_serverless_pg.database_port
      DATABASE_NAME   = module.aurora_serverless_pg.database_name
      DB_POOL_SIZE    = "2"
      DB_POOL_RECYCLE = "3600"
      # SSM Parameter Store paths for credentials
      DB_USERNAME_SSM_PARAM = module.aurora_serverless_pg.db_username_parameter_name
      DB_PASSWORD_SSM_PARAM = module.aurora_serverless_pg.db_password_parameter_name

      LEGAL_AGENT_FUNCTION_NAME = module.tf_lambda_legal_agent.lambda_function_name
      BEDROCK_REGION = var.bedrock_region
    }
  )
}



########################################################################################
#######################################################################
# Legal Agent Lambda Function
###############################################################################################
########################################################################################


module "tf_lambda_legal_agent" {
  source         = "../tf-modules/tf-lambda"
  env            = var.env
  region         = var.resource_region
  lambda_name    = "${var.project_name}-legal-agent"
  lambda_src_dir = "agents/legal"
  lambda_timeout = 300  # 5 minutes for LLM operations


  # Attach Aurora access policy to Lambda's own role
  additional_iam_policy_arns = [
    module.aurora_serverless_pg.aurora_access_policy_arn,
    aws_iam_policy.s3_vector_access_policy.arn,
    aws_iam_policy.lambda_sagemaker_access_policy.arn,
    aws_iam_policy.bedrock_invoke_policy.arn,
  ]

  # VPC configuration to access Aurora in private subnets
  vpc_subnet_ids         = data.aws_subnets.default.ids
  vpc_security_group_ids = [module.aurora_serverless_pg.lambda_security_group_id]

  environment_variables = merge(
    {
      ENV       = var.env
      LOG_LEVEL = var.log_level
    },
    # Database configuration from Aurora Serverless module outputs
    {
      DATABASE_HOST   = module.aurora_serverless_pg.aurora_cluster_endpoint
      DATABASE_PORT   = module.aurora_serverless_pg.database_port
      DATABASE_NAME   = module.aurora_serverless_pg.database_name
      DB_POOL_SIZE    = "2"
      DB_POOL_RECYCLE = "3600"
      # SSM Parameter Store paths for credentials
      DB_USERNAME_SSM_PARAM = module.aurora_serverless_pg.db_username_parameter_name
      DB_PASSWORD_SSM_PARAM = module.aurora_serverless_pg.db_password_parameter_name

      BEDROCK_REGION = var.bedrock_region
    }
  )
}