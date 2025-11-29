# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "${local.resource_name_prefix_hyphenated}-backend-api-gateway"
  protocol_type = "HTTP"

  cors_configuration {
    allow_credentials = false  # Cannot be true when allow_origins is "*"
    allow_headers     = ["authorization", "content-type", "x-amz-date", "x-api-key", "x-amz-security-token"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins     = ["*"]  # CORS is handled in Lambda via environment variables
    max_age           = 300
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 100
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = module.tf_lambda_backend_api.lambda_function_invoke_arn
}

# API Gateway Routes - all routes under /api/*
resource "aws_apigatewayv2_route" "api_any" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /api/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"

  # No authorization at API Gateway level - handled in Lambda
}

# OPTIONS route for CORS preflight (no auth needed)
resource "aws_apigatewayv2_route" "api_options" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "OPTIONS /api/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.tf_lambda_backend_api.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}