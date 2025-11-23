module "aurora_serverless_pg" {
  source            = "../tf-modules/aurora-serverless-pg"
  env               = var.env
  region            = var.resource_region
  project_name      = var.project_name
  db_admin_username = "adminuser"
  db_name           = "real_estate_agents"
}


# ========================================
# ECR Repository
# ========================================

# ECR repository for the lambda Docker image
# resource "aws_ecr_repository" "agentic_ai" {
#   name                 = "${local.resource_name_prefix_hyphenated}-agentic-ai"
#   image_tag_mutability = "MUTABLE"
#   force_delete         = true # Allow deletion even with images

#   image_scanning_configuration {
#     scan_on_push = false
#   }
# }
