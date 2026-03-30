.PHONY: up down build migrate seed test lint logs logs-api logs-worker restart-api psql \
       aws-prod-init aws-prod-plan aws-prod-apply aws-prod-build-push aws-prod-redeploy \
       aws-prod-deploy aws-prod-migrate aws-prod-seed aws-prod-smoke aws-prod-logs

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
	cd frontend && npx eslint .

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
# AWS Production / Staging
# ──────────────────────────────────────────────
TF_DIR := infra/terraform
TF_VARS := -var-file=env/prod.tfvars

aws-prod-init:
	cd $(TF_DIR) && terraform init

aws-prod-plan:
	cd $(TF_DIR) && terraform plan $(TF_VARS)

aws-prod-apply:
	cd $(TF_DIR) && terraform apply $(TF_VARS) -auto-approve

aws-prod-build-push:
	./scripts/deploy/aws/build_and_push.sh

aws-prod-redeploy:
	./scripts/deploy/aws/build_and_push.sh --deploy

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

aws-prod-smoke:
	@echo "==> Smoke testing endpoints..."
	$(eval API_URL := $(shell cd $(TF_DIR) && terraform output -raw api_url))
	$(eval WEB_URL := $(shell cd $(TF_DIR) && terraform output -raw web_url))
	@curl -sf "$(API_URL)/health" && echo "  API /health: OK" || echo "  API /health: FAIL"
	@curl -sf "$(WEB_URL)" > /dev/null && echo "  Web /:       OK" || echo "  Web /:       FAIL"

aws-prod-logs:
	@echo "==> Tailing API logs..."
	aws logs tail /ecs/saf-logistic-prod-api --follow --since 5m
