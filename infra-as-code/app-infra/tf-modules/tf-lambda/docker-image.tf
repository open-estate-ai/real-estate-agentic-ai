########################
# Build & push Docker image (Dockerfile.lambda)
########################

resource "null_resource" "build_and_push_image" {
  triggers = {
    src_hash = local.lambda_src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e

      AWS_REGION="${var.region}"
      REPO_URL="${aws_ecr_repository.lambda.repository_url}"
      IMAGE_TAG="${local.image_tag}"
      LAMBDA_SRC_DIR="${local.lambda_src_abs_dir}"
      BACKEND_DIR="${local.lambda_backend_abs_dir}"
      
      echo "Logging in to ECR..."
      # Use --password-stdin with explicit error handling for keychain conflicts
      aws ecr get-login-password --region "$AWS_REGION" \
        | docker login --username AWS --password-stdin "$REPO_URL" 2>&1 || {
          # If login fails due to keychain conflict, continue anyway (credentials may already be cached)
          echo "Warning: Docker login encountered an issue, but continuing (credentials may be cached)"
        }

      echo "Building linux/amd64 image using buildx..."
      # Use a unique builder name per Lambda to avoid conflicts
      BUILDER_NAME="lambda_builder_${var.lambda_name}"
      docker buildx create --use --name "$BUILDER_NAME" 2>/dev/null || docker buildx use "$BUILDER_NAME"

      echo "Building linux/amd64 image..."
      docker build \
        --platform linux/amd64 \
        -f "$LAMBDA_SRC_DIR/Dockerfile.lambda" \
        -t "$REPO_URL:$IMAGE_TAG" \
        "$BACKEND_DIR"

      echo "Pushing Docker image to $REPO_URL:$IMAGE_TAG"
      docker push "$REPO_URL:$IMAGE_TAG"
    EOT

    interpreter = ["/bin/bash", "-c"]
  }
}
