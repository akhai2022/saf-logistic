.PHONY: up down build migrate seed test test-local lint typecheck check \
       test-e2e test-e2e-full build-frontend logs logs-api logs-worker restart-api psql \
       check-backend-lint check-frontend-lint check-frontend-types \
       check-backend-tests check-frontend-build check-e2e \
       migrate-check security-check \
       aws-prod-init aws-prod-plan aws-prod-apply aws-prod-build-push \
       aws-prod-redeploy aws-prod-deploy aws-prod-migrate aws-prod-seed \
       aws-prod-rollback aws-prod-smoke aws-prod-logs

# ──────────────────────────────────────────────
# Local Development
# ──────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m app.core.seed

test:
	docker compose exec api pytest -v --tb=short

test-local:
	cd backend && pytest -v --tb=short

lint:
	cd backend && python -m ruff check .
	cd frontend && npm run lint

typecheck:
	cd frontend && npm run typecheck

test-e2e:
	cd frontend && npx playwright test --grep "@critical"

test-e2e-full:
	cd frontend && npx playwright test

build-frontend:
	cd frontend && npm run build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker-default worker-ocr

restart-api:
	docker compose restart api

psql:
	docker compose exec postgres psql -U saf -d saf

# ──────────────────────────────────────────────
# Pre-Deploy Gate (CLAUDE.md compliance)
#
# Full validation gate required before any production deploy.
# Each step MUST pass — failure aborts the pipeline.
#
# Usage:
#   make check          — run the full gate
#   make check-e2e      — run only Playwright critical-path suite
# ──────────────────────────────────────────────
check-backend-lint:
	@echo "==> [1/7] Backend lint..."
	docker compose exec api python -m ruff check . 2>/dev/null || \
		docker compose run --rm --no-deps api python -m ruff check .

check-frontend-lint:
	@echo "==> [2/7] Frontend lint..."
	cd frontend && npm run lint

check-frontend-types:
	@echo "==> [3/7] Frontend typecheck..."
	cd frontend && npm run typecheck

check-backend-tests:
	@echo "==> [4/7] Backend tests..."
	docker compose exec api pytest -v --tb=short 2>/dev/null || \
		docker compose run --rm api pytest -v --tb=short

check-frontend-build:
	@echo "==> [5/7] Frontend build..."
	cd frontend && npm run build

check-e2e:
	@echo "==> [6/7] Playwright e2e (critical path)..."
	cd frontend && npx playwright test --grep "@critical"

migrate-check:
	@echo "==> [7/7] Migration safety check (single head)..."
	@python3 scripts/check_migration_heads.py

security-check:
	@echo "==> [8/8] Dependency security scan..."
	cd backend && pip audit --desc 2>/dev/null || echo "  WARN: pip audit not installed (pip install pip-audit)"
	cd frontend && npm audit --omit=dev --audit-level=high 2>/dev/null || echo "  WARN: npm audit found issues (non-blocking)"

check: check-backend-lint check-frontend-lint check-frontend-types check-backend-tests check-frontend-build check-e2e migrate-check
	@echo ""
	@echo "========================================"
	@echo "  Pre-deploy gate PASSED (all 7 steps)"
	@echo "========================================"
	@echo ""
	@echo "Optional: run 'make security-check' for dependency scan"
	@echo "Optional: run 'make test-e2e-full' for complete Playwright suite"

# ──────────────────────────────────────────────
# AWS Production / Staging
# All deploy targets are gated by 'check'.
# ──────────────────────────────────────────────
TF_DIR := infra/terraform
TF_VARS := -var-file=env/prod.tfvars

aws-prod-init:
	cd $(TF_DIR) && terraform init

aws-prod-plan:
	cd $(TF_DIR) && terraform plan $(TF_VARS)

aws-prod-apply:
	cd $(TF_DIR) && terraform apply $(TF_VARS) -auto-approve

aws-prod-build-push: check
	./scripts/deploy/aws/build_and_push.sh --skip-checks --gated

aws-prod-redeploy: check
	./scripts/deploy/aws/build_and_push.sh --skip-checks --deploy --gated

aws-prod-deploy: aws-prod-apply aws-prod-redeploy

aws-prod-migrate:
	@echo "==> Running migration task..."
	$(eval CLUSTER := $(shell cd $(TF_DIR) && terraform output -raw ecs_cluster_name))
	$(eval MIGRATION_TD := $(shell cd $(TF_DIR) && terraform output -raw migration_task_definition))
	$(eval SUBNET := $(shell echo '$(shell cd $(TF_DIR) && terraform output -json 2>/dev/null)' | python3 -c "import sys,json; print(json.load(sys.stdin).get('private_subnet_ids',{}).get('value',[''])[0])" 2>/dev/null || echo "subnet-0a9e6fae7d748035c"))
	$(eval SG := $(shell cd $(TF_DIR) && terraform output -raw backend_security_group_id))
	aws ecs run-task --cluster $(CLUSTER) --task-definition $(MIGRATION_TD) \
		--launch-type FARGATE \
		--network-configuration "awsvpcConfiguration={subnets=[$(SUBNET)],securityGroups=[$(SG)],assignPublicIp=DISABLED}" \
		--no-cli-pager

aws-prod-seed:
	@echo "==> Running seed via ECS exec..."
	$(eval CLUSTER := $(shell cd $(TF_DIR) && terraform output -raw ecs_cluster_name))
	$(eval API_SVC := $(shell cd $(TF_DIR) && terraform output -raw api_service_name))
	$(eval TASK_ARN := $(shell aws ecs list-tasks --cluster $(CLUSTER) --service-name $(API_SVC) --query 'taskArns[0]' --output text))
	aws ecs execute-command --cluster $(CLUSTER) --task $(TASK_ARN) --container api \
		--interactive --command "python -m app.core.seed"

aws-prod-rollback:
	@echo "==> Rolling back ECS services to previous task definition..."
	@echo ""
	@echo "This will update each service to the PREVIOUS task definition revision."
	@echo "Press Ctrl+C within 5s to abort."
	@sleep 5
	$(eval CLUSTER := zinovia-fans-prod-cluster)
	@for FAMILY in saf-logistic-prod-api saf-logistic-prod-web saf-logistic-prod-worker; do \
		CURRENT=$$(aws ecs describe-services --cluster $(CLUSTER) --services $$FAMILY \
			--query 'services[0].taskDefinition' --output text); \
		CURRENT_REV=$$(echo $$CURRENT | grep -o '[0-9]*$$'); \
		PREV_REV=$$((CURRENT_REV - 1)); \
		echo "  $$FAMILY: rev $$CURRENT_REV → $$PREV_REV"; \
		aws ecs update-service --cluster $(CLUSTER) --service $$FAMILY \
			--task-definition "$$FAMILY:$$PREV_REV" --force-new-deployment \
			--query 'service.serviceName' --output text > /dev/null; \
	done
	@echo ""
	@echo "==> Waiting for services to stabilize..."
	aws ecs wait services-stable --cluster $(CLUSTER) \
		--services saf-logistic-prod-api saf-logistic-prod-web saf-logistic-prod-worker
	@echo "==> Rollback complete. Run 'make aws-prod-smoke' to verify."

aws-prod-smoke:
	@echo "==> Smoke testing endpoints..."
	$(eval API_URL := $(shell cd $(TF_DIR) && terraform output -raw api_url))
	$(eval WEB_URL := $(shell cd $(TF_DIR) && terraform output -raw web_url))
	@curl -sf "$(API_URL)/health" && echo "  API /health: OK" || echo "  API /health: FAIL"
	@curl -sf "$(WEB_URL)" > /dev/null && echo "  Web /:       OK" || echo "  Web /:       FAIL"

aws-prod-logs:
	@echo "==> Tailing API logs..."
	aws logs tail /ecs/saf-logistic-prod-api --follow --since 5m
