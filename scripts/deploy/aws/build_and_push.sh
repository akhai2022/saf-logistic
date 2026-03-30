#!/usr/bin/env bash
# ──────────────────────────────────────────────
# SAF-Logistic — Build & Push Docker images to ECR
#
# Tag strategy:
#   - Each image is tagged with the git short SHA + "latest" + "prod-latest"
#   - ECS task definitions are updated to use the new git SHA tag
#   - "latest" and "prod-latest" are convenience aliases
#
# Usage:
#   ./build_and_push.sh          # build + push only
#   ./build_and_push.sh --deploy # build + push + update ECS task defs + force redeploy
# ──────────────────────────────────────────────
set -euo pipefail

DEPLOY=false
[[ "${1:-}" == "--deploy" ]] && DEPLOY=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

REGION="us-east-1"
ACCOUNT_ID="208030346312"
CLUSTER="zinovia-fans-prod-cluster"

# ECR repo names (must match ECS task definitions)
API_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/zinovia-fans-prod-api"
WEB_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/zinovia-fans-prod-web"

# API URL baked into Next.js bundle at build time
cd "$TF_DIR"
API_URL=$(terraform output -raw api_url)
cd "$ROOT_DIR"

TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "╔═══════════════════════════════════════════╗"
echo "║  SAF-Logistic Deploy                      ║"
echo "╠═══════════════════════════════════════════╣"
echo "║  Git tag:  $TAG"
echo "║  API repo: zinovia-fans-prod-api"
echo "║  Web repo: zinovia-fans-prod-web"
echo "║  API URL:  $API_URL"
echo "║  Deploy:   $DEPLOY"
echo "╚═══════════════════════════════════════════╝"
echo ""

echo "==> Logging into ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# ── Build & Push API ─────────────────────────────────────────────
echo ""
echo "==> Building API image..."
docker build --network host \
  -f backend/Dockerfile.api \
  -t "${API_REPO}:${TAG}" \
  -t "${API_REPO}:latest" \
  -t "${API_REPO}:prod-latest" \
  backend/

echo "==> Pushing API image..."
docker push "${API_REPO}:${TAG}"
docker push "${API_REPO}:latest"
docker push "${API_REPO}:prod-latest"

# ── Build & Push Web ─────────────────────────────────────────────
echo ""
echo "==> Building Web image..."
docker build --network host \
  -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL="${API_URL}" \
  -t "${WEB_REPO}:${TAG}" \
  -t "${WEB_REPO}:latest" \
  -t "${WEB_REPO}:prod-latest" \
  frontend/

echo "==> Pushing Web image..."
docker push "${WEB_REPO}:${TAG}"
docker push "${WEB_REPO}:latest"
docker push "${WEB_REPO}:prod-latest"

echo ""
echo "==> Images pushed:"
echo "    API: ${API_REPO}:${TAG}"
echo "    Web: ${WEB_REPO}:${TAG}"

# ── Deploy to ECS (if --deploy flag) ─────────────────────────────
if [ "$DEPLOY" = true ]; then
  echo ""
  echo "==> Updating ECS task definitions to tag: ${TAG}..."

  for FAMILY in zinovia-fans-prod-api zinovia-fans-prod-web; do
    if [ "$FAMILY" = "zinovia-fans-prod-api" ]; then
      NEW_IMAGE="${API_REPO}:${TAG}"
    else
      NEW_IMAGE="${WEB_REPO}:${TAG}"
    fi

    # Get current task def, update image tag, register new revision
    CURRENT_TD=$(aws ecs describe-task-definition --task-definition "$FAMILY" --output json)
    NEW_TD=$(echo "$CURRENT_TD" | python3 -c "
import sys, json
td = json.load(sys.stdin)['taskDefinition']
td['containerDefinitions'][0]['image'] = '${NEW_IMAGE}'
for k in ['taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy','deregisteredAt']:
    td.pop(k, None)
print(json.dumps(td))
")
    REV=$(echo "$NEW_TD" | aws ecs register-task-definition --cli-input-json file:///dev/stdin \
      --query 'taskDefinition.revision' --output text)
    echo "    ${FAMILY}: registered revision ${REV} with image ${NEW_IMAGE}"

    # Map family to service name (same name in this setup)
    aws ecs update-service --cluster "$CLUSTER" --service "$FAMILY" \
      --task-definition "${FAMILY}:${REV}" --force-new-deployment \
      --query 'service.serviceName' --output text > /dev/null
  done

  echo ""
  echo "==> Waiting for services to stabilize..."
  aws ecs wait services-stable --cluster "$CLUSTER" \
    --services zinovia-fans-prod-api zinovia-fans-prod-web

  echo ""
  echo "╔═══════════════════════════════════════════╗"
  echo "║  Deploy complete!                         ║"
  echo "║  Tag: ${TAG}                              "
  echo "║  Both services stable.                    ║"
  echo "╚═══════════════════════════════════════════╝"
else
  echo ""
  echo "Images pushed. Run with --deploy to also update ECS."
  echo "Or run: make aws-prod-redeploy"
fi
