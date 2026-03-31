#!/usr/bin/env bash
# ──────────────────────────────────────────────
# SAF-Logistic — Initialize database on shared RDS
# Creates the database, runs migrations, and seeds demo data.
#
# Prerequisites:
#   - AWS CLI configured
#   - Terraform outputs available
#   - psql client installed
#   - ECS services running (API must be up for seed via exec)
#
# Usage:
#   ./scripts/deploy/aws/init_database.sh
# ──────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

echo "==> SAF-Logistic Database Initialization"
echo ""

# ── Step 1: Create database on shared RDS ──
echo "==> Step 1: Create database 'saf_logistic' on shared RDS"
echo "    You need to connect to the RDS instance and run:"
echo ""
echo "    CREATE DATABASE saf_logistic;"
echo "    CREATE USER saf_app WITH PASSWORD '<password>';"
echo "    GRANT ALL PRIVILEGES ON DATABASE saf_logistic TO saf_app;"
echo "    \\c saf_logistic"
echo "    GRANT ALL ON SCHEMA public TO saf_app;"
echo ""
echo "    To connect via ECS exec (using an existing API container):"
echo "    aws ecs execute-command --cluster zinovia-fans-prod-cluster \\"
echo "      --task <TASK_ARN> --container api --interactive \\"
echo "      --command 'python -c \"import asyncio; from app.core.db import engine; print(engine.url)\"'"
echo ""
read -p "    Press Enter once the database is created (or Ctrl+C to abort)..."

# ── Step 2: Store DATABASE_URL in Secrets Manager ──
echo ""
echo "==> Step 2: Store DATABASE_URL in Secrets Manager"
read -p "    Enter the full DATABASE_URL (postgresql+asyncpg://saf_app:PASS@host:5432/saf_logistic): " DB_URL

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL is required."
  exit 1
fi

# Validate that the URL points to saf_logistic database
if ! echo "$DB_URL" | grep -q '/saf_logistic$'; then
  echo "ERROR: DATABASE_URL must end with /saf_logistic"
  echo "       Got: $DB_URL"
  echo "       The URL must point to the saf_logistic database, not zinovia or another DB."
  exit 1
fi

aws secretsmanager put-secret-value \
  --secret-id "saf-logistic-prod/database-url" \
  --secret-string "$DB_URL" \
  --no-cli-pager
echo "    Done."

# ── Step 3: Store APP_SECRET_KEY in Secrets Manager ──
echo ""
echo "==> Step 3: Store APP_SECRET_KEY in Secrets Manager"
APP_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo "    Generated key: ${APP_KEY:0:16}..."

aws secretsmanager put-secret-value \
  --secret-id "saf-logistic-prod/app-secret-key" \
  --secret-string "$APP_KEY" \
  --no-cli-pager
echo "    Done."

# ── Step 4: Run migrations via ECS RunTask ──
echo ""
echo "==> Step 4: Running database migrations..."
cd "$TF_DIR"
CLUSTER=$(terraform output -raw ecs_cluster_name)
MIGRATION_TD=$(terraform output -raw migration_task_definition)
SG=$(terraform output -raw backend_security_group_id)
SUBNET="subnet-0a9e6fae7d748035c"
cd "$ROOT_DIR"

TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --task-definition "$MIGRATION_TD" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
  --query 'tasks[0].taskArn' --output text \
  --no-cli-pager)

echo "    Migration task started: $TASK_ARN"
echo "    Waiting for task to complete..."
aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$TASK_ARN"

EXIT_CODE=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].exitCode' --output text --no-cli-pager)

if [ "$EXIT_CODE" = "0" ]; then
  echo "    Migrations completed successfully."
else
  echo "    ERROR: Migration failed with exit code $EXIT_CODE"
  echo "    Check logs: aws logs tail /ecs/saf-logistic-prod-migration --since 10m"
  exit 1
fi

# ── Step 5: Force redeploy API (to pick up secrets) ──
echo ""
echo "==> Step 5: Redeploying API service..."
API_SVC=$(cd "$TF_DIR" && terraform output -raw api_service_name)
aws ecs update-service --cluster "$CLUSTER" --service "$API_SVC" --force-new-deployment --no-cli-pager > /dev/null
echo "    Waiting for API stability..."
aws ecs wait services-stable --cluster "$CLUSTER" --services "$API_SVC"
echo "    API service stable."

# ── Step 6: Seed demo data ──
echo ""
echo "==> Step 6: Seeding demo data..."
sleep 5  # give the container a moment to fully start

TASK_ARN=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$API_SVC" \
  --query 'taskArns[0]' --output text --no-cli-pager)

aws ecs execute-command \
  --cluster "$CLUSTER" \
  --task "$TASK_ARN" \
  --container api \
  --interactive \
  --command "python -m app.core.seed"

echo ""
echo "==> Database initialization complete!"
echo ""
echo "    Web URL:  https://saf.dataforgeai.fr"
echo "    API URL:  https://api-saf.dataforgeai.fr"
echo "    API Docs: https://api-saf.dataforgeai.fr/docs"
echo ""
echo "    Login credentials:"
echo "    ┌─────────────────────────────┬──────────────────┬──────────────┐"
echo "    │ Email                       │ Password         │ Role         │"
echo "    ├─────────────────────────────┼──────────────────┼──────────────┤"
echo "    │ admin@saf.local             │ admin            │ Super Admin  │"
echo "    │ dirigeant@saf.local         │ dirigeant2026    │ Dirigeant    │"
echo "    │ exploitant@saf.local        │ exploit2026      │ Exploitation │"
echo "    │ compta@saf.local            │ compta2026       │ Comptabilité │"
echo "    │ rh@saf.local                │ rh2026           │ RH Paie      │"
echo "    │ flotte@saf.local            │ flotte2026       │ Flotte       │"
echo "    │ auditeur@saf.local          │ audit2026        │ Lecture seule│"
echo "    └─────────────────────────────┴──────────────────┴──────────────┘"
echo ""
echo "    Tenant ID: 00000000-0000-0000-0000-000000000001"
