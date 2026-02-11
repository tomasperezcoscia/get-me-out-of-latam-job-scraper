.PHONY: help docker-up docker-down collect stats review export migrate seed test lint frontend-install frontend-dev frontend-build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

docker-up: ## Start PostgreSQL + Redis containers
	docker compose up -d

docker-down: ## Stop containers
	docker compose down

collect: ## Collect jobs from all sources
	.venv/Scripts/python -m cli.commands collect --all

collect-dry: ## Dry-run collection (fetch but don't save)
	.venv/Scripts/python -m cli.commands collect --all --dry-run

stats: ## Show job statistics
	.venv/Scripts/python -m cli.commands stats

review: ## Interactive job review
	.venv/Scripts/python -m cli.commands review

export-csv: ## Export all jobs to CSV
	.venv/Scripts/python -m cli.commands export --format csv -o data/exports/jobs.csv

export-json: ## Export all jobs to JSON
	.venv/Scripts/python -m cli.commands export --format json -o data/exports/jobs.json

migrate: ## Run Alembic migrations
	.venv/Scripts/python -m alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new MSG="description")
	.venv/Scripts/python -m alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed user profile
	.venv/Scripts/python scripts/seed_profile.py

test: ## Run tests
	.venv/Scripts/python -m pytest tests/ -v

lint: ## Run ruff linter
	.venv/Scripts/python -m ruff check app/ cli/ scripts/ tests/

lint-fix: ## Auto-fix lint issues
	.venv/Scripts/python -m ruff check --fix app/ cli/ scripts/ tests/

install: ## Install dependencies
	uv pip install -e ".[dev]"

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build
