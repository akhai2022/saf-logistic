#!/usr/bin/env bash
# ──────────────────────────────────────────────
# SAF-Logistic — Build & Push Docker images to ECR
# ──────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

echo "==> Retrieving ECR URLs from Terraform outputs..."
cd "$TF_DIR"
API_REPO=$(terraform output -raw ecr_api_url)
WEB_REPO=$(terraform output -raw ecr_web_url)
API_URL=$(terraform output -raw api_url)
WEB_URL=$(terraform output -raw web_url)
REGION=$(terraform output -raw 2>/dev/null | grep -q aws_region && terraform output -raw aws_region || echo "us-east-1")
cd "$ROOT_DIR"

TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
ACCOUNT_ID=$(echo "$API_REPO" | cut -d. -f1)

echo "==> ECR API:  $API_REPO"
echo "==> ECR Web:  $WEB_REPO"
echo "==> Tag:      $TAG"
echo "==> API URL:  $API_URL"
echo "==> Web URL:  $WEB_URL"

echo ""
echo "==> Logging into ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo ""
echo "==> Building API image..."
docker buildx build --platform linux/amd64 \
  -f backend/Dockerfile.api \
  -t "${API_REPO}:${TAG}" \
  -t "${API_REPO}:latest" \
  --push \
  backend/

echo ""
echo "==> Building Web image..."
docker buildx build --platform linux/amd64 \
  -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL="${API_URL}" \
  -t "${WEB_REPO}:${TAG}" \
  -t "${WEB_REPO}:latest" \
  --push \
  frontend/

echo ""
echo "==> Done! Images pushed:"
echo "    API: ${API_REPO}:${TAG}"
echo "    Web: ${WEB_REPO}:${TAG}"
