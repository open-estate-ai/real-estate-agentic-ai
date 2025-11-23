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
      aws ecr get-login-password --region "$AWS_REGION" \
        | docker login --username AWS --password-stdin "$REPO_URL"

      echo "Building linux/amd64 image using buildx..."
      docker buildx create --use --name lambda_builder || true

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
