.PHONY: up down build migrate seed test lint

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
