#!/usr/bin/env bash
# ──────────────────────────────────────────────
# SAF-Logistic — Build & Push Docker images to ECR
# ──────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

echo "==> Retrieving ECR URLs from ECS task definitions (source of truth)..."
REGION="us-east-1"
ACCOUNT_ID="208030346312"

# Get actual ECR repo URLs from running ECS task definitions
API_REPO=$(aws ecs describe-task-definition --task-definition zinovia-fans-prod-api \
  --query 'taskDefinition.containerDefinitions[0].image' --output text | sed 's/:.*$//')
WEB_REPO=$(aws ecs describe-task-definition --task-definition zinovia-fans-prod-web \
  --query 'taskDefinition.containerDefinitions[0].image' --output text | sed 's/:.*$//')

# API URL from terraform (build arg for Next.js)
cd "$TF_DIR"
API_URL=$(terraform output -raw api_url)
cd "$ROOT_DIR"

TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "==> ECR API:  $API_REPO"
echo "==> ECR Web:  $WEB_REPO"
echo "==> Tag:      $TAG"
echo "==> API URL:  $API_URL"

echo ""
echo "==> Logging into ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo ""
echo "==> Building API image..."
docker build --network host \
  -f backend/Dockerfile.api \
  -t "${API_REPO}:${TAG}" \
  -t "${API_REPO}:latest" \
  backend/

echo "==> Pushing API image..."
docker push "${API_REPO}:${TAG}"
docker push "${API_REPO}:latest"

echo ""
echo "==> Building Web image..."
docker build --network host \
  -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL="${API_URL}" \
  -t "${WEB_REPO}:${TAG}" \
  -t "${WEB_REPO}:latest" \
  frontend/

echo "==> Pushing Web image..."
docker push "${WEB_REPO}:${TAG}"
docker push "${WEB_REPO}:latest"

echo ""
echo "==> Done! Images pushed:"
echo "    API: ${API_REPO}:${TAG}"
echo "    Web: ${WEB_REPO}:${TAG}"
