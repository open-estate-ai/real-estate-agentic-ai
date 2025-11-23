## TEMPORARILY COMMENTED OUT RESOURCES ##
module "aurora_serverless_pg" {
  source            = "../tf-modules/aurora-serverless-pg"
  env               = var.env
  region            = var.resource_region
  project_name      = var.project_name
  db_admin_username = "adminuser"
  db_name           = "real_estate_agents"
}



module "tf_lambda_backend_api" {
  source         = "../tf-modules/tf-lambda"
  env            = var.env
  region         = var.resource_region
  lambda_name    = "${var.project_name}-backend-api"
  lambda_src_dir = "api"

  # Attach Aurora access policy to Lambda's own role
  additional_iam_policy_arns = [module.aurora_serverless_pg.aurora_access_policy_arn]

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
      DATABASE_USER   = module.aurora_serverless_pg.iam_database_user
      DB_POOL_SIZE    = "2"
      DB_POOL_RECYCLE = "3600"
      # Lambda always uses IAM auth - no password needed
    },
    # Only add planner agent URL if configured
    var.planner_agent_url != "" ? {
      PLANNER_AGENT_URL = var.planner_agent_url
    } : {}
  )
}
