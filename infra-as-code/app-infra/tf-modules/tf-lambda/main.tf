# ========================================
# ECR Repository
# ========================================

# ECR repository for the lambda Docker image
resource "aws_ecr_repository" "lambda" {
  name                 = local.resource_name_prefix_hyphenated
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Allow deletion even with images

  image_scanning_configuration {
    scan_on_push = false
  }
}


#========================================
# IAM Role for Lambda
#========================================

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "lambda_role" {
  name               = "${local.resource_name_prefix_hyphenated}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach additional IAM policies (e.g., Aurora access)
resource "aws_iam_role_policy_attachment" "additional_policies" {
  count      = length(var.additional_iam_policy_arns)
  role       = aws_iam_role.lambda_role.name
  policy_arn = var.additional_iam_policy_arns[count.index]
}

########################
# CloudWatch log group
########################

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${local.resource_name_prefix_hyphenated}"
  retention_in_days = 7
}

########################
# Lambda function using image from ECR
########################
resource "aws_lambda_function" "docker_image_lambda" {
  function_name = local.resource_name_prefix_hyphenated
  role          = aws_iam_role.lambda_role.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda.repository_url}:${local.image_tag}"

  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  architectures = ["x86_64"] # change to ["arm64"] if your image is arm

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [1] : []
    content {
      variables = var.environment_variables
    }
  }

  depends_on = [
    null_resource.build_and_push_image,
    aws_iam_role_policy_attachment.lambda_basic_logs,
    aws_iam_role_policy_attachment.additional_policies
  ]
}
