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
SKIP_CHECKS=false
GATED=false
for arg in "$@"; do
  case "$arg" in
    --deploy) DEPLOY=true ;;
    --skip-checks) SKIP_CHECKS=true ;;
    --gated) GATED=true ;;  # Set by Makefile after 'make check' passed
  esac
done

# --skip-checks is only allowed when called from the Makefile gate (--gated)
if [ "$SKIP_CHECKS" = true ] && [ "$GATED" = false ]; then
  echo "ERROR: --skip-checks requires the Makefile pre-deploy gate."
  echo "       Use 'make aws-prod-build-push' or 'make aws-prod-redeploy'."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

# ── Pre-flight validation ────────────────────────────────────────
if [ "$SKIP_CHECKS" = false ]; then
  echo "==> Running pre-flight checks..."

  echo "    [1/3] Frontend lint..."
  (cd "$ROOT_DIR/frontend" && npx next lint --max-warnings 0 --quiet) || {
    echo "ERROR: Frontend lint failed."
    exit 1
  }

  echo "    [2/3] Frontend typecheck..."
  (cd "$ROOT_DIR/frontend" && npx tsc --noEmit) || {
    echo "ERROR: TypeScript errors found."
    exit 1
  }

  echo "    [3/3] Frontend build..."
  (cd "$ROOT_DIR/frontend" && npm run build --quiet) || {
    echo "ERROR: Frontend build failed."
    exit 1
  }

  echo "    All pre-flight checks passed."
  echo ""
else
  echo "==> Pre-flight checks SKIPPED (--skip-checks flag, non-deploy build)."
  echo ""
fi

REGION="us-east-1"
ACCOUNT_ID="208030346312"
CLUSTER="zinovia-fans-prod-cluster"

# ECR repo names (must match ECS task definitions)
API_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/saf-logistic-prod-api"
WEB_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/saf-logistic-prod-web"

# API URL baked into Next.js bundle at build time
cd "$TF_DIR"
API_URL=$(terraform output -raw api_url)
cd "$ROOT_DIR"

TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "╔═══════════════════════════════════════════╗"
echo "║  SAF-Logistic Deploy                      ║"
echo "╠═══════════════════════════════════════════╣"
echo "║  Git tag:  $TAG"
echo "║  API repo: saf-logistic-prod-api"
echo "║  Web repo: saf-logistic-prod-web"
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

  for FAMILY in saf-logistic-prod-api saf-logistic-prod-web saf-logistic-prod-worker; do
    case "$FAMILY" in
      saf-logistic-prod-api|saf-logistic-prod-worker)
        NEW_IMAGE="${API_REPO}:${TAG}" ;;
      saf-logistic-prod-web)
        NEW_IMAGE="${WEB_REPO}:${TAG}" ;;
    esac

    # Get current task def, update image tag, register new revision
    TMPFILE=$(mktemp /tmp/td-XXXXXX.json)
    aws ecs describe-task-definition --task-definition "$FAMILY" --output json | python3 -c "
import sys, json
td = json.load(sys.stdin)['taskDefinition']
td['containerDefinitions'][0]['image'] = '${NEW_IMAGE}'
for k in ['taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy','deregisteredAt']:
    td.pop(k, None)
json.dump(td, open('${TMPFILE}', 'w'))
"
    REV=$(aws ecs register-task-definition --cli-input-json "file://${TMPFILE}" \
      --query 'taskDefinition.revision' --output text)
    rm -f "$TMPFILE"
    echo "    ${FAMILY}: registered revision ${REV} with image ${NEW_IMAGE}"

    # Map family to service name (same name in this setup)
    aws ecs update-service --cluster "$CLUSTER" --service "$FAMILY" \
      --task-definition "${FAMILY}:${REV}" --force-new-deployment \
      --query 'service.serviceName' --output text > /dev/null
  done

  echo ""
  echo "==> Waiting for services to stabilize..."
  aws ecs wait services-stable --cluster "$CLUSTER" \
    --services saf-logistic-prod-api saf-logistic-prod-web saf-logistic-prod-worker

  echo ""
  echo "╔═══════════════════════════════════════════╗"
  echo "║  Deploy complete!                         ║"
  echo "║  Tag: ${TAG}                              "
  echo "║  All services stable.                     ║"
  echo "╚═══════════════════════════════════════════╝"
else
  echo ""
  echo "Images pushed. Run with --deploy to also update ECS."
  echo "Or run: make aws-prod-redeploy"
fi
