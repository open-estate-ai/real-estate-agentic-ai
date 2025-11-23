## TEMPORARILY COMMENTED OUT RESOURCES ##
# module "aurora_serverless_pg" {
#   source            = "../tf-modules/aurora-serverless-pg"
#   env               = var.env
#   region            = var.resource_region
#   project_name      = var.project_name
#   db_admin_username = "adminuser"
#   db_name           = "real_estate_agents"
# }



module "tf_lambda_backend_api" {
  source         = "../tf-modules/tf-lambda"
  env            = var.env
  region         = var.resource_region
  lambda_name    = "${var.project_name}-backend-api"
  lambda_src_dir = "api"
}
