.DEFAULT_GOAL := help
UV ?= uv

.PHONY: help install up down logs run migrate seed test lint format typecheck audit erd check-commits

help: ## Show this help
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Install dependencies and git hooks
	$(UV) sync --frozen
	$(UV) run pre-commit install

up: ## Start the app and database with Docker Compose
	docker compose up --build -d
	@echo "datakyt is starting on http://localhost:8000 (docker compose logs -f app)"

down: ## Stop the Compose stack
	docker compose down

logs: ## Follow application logs
	docker compose logs -f app

run: ## Run the dev server against DATAKYT_* settings
	$(UV) run datakyt migrate
	$(UV) run datakyt serve --reload

migrate: ## Apply database migrations
	$(UV) run datakyt migrate

seed: ## Load demo data into an empty database
	$(UV) run datakyt seed

test: ## Run tests with coverage (Postgres via DATAKYT_TEST_DATABASE_URL or testcontainers)
	$(UV) run pytest --cov --cov-report=term-missing

lint: ## Run ruff, the formatter check, mypy and the ERD drift check
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy
	$(UV) run python scripts/generate_erd.py --check

format: ## Apply ruff fixes and formatting
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

audit: ## Check locked dependencies for known vulnerabilities
	$(UV) export --frozen --no-dev --no-emit-project --format requirements-txt > .audit-requirements.txt
	$(UV) run pip-audit --strict --disable-pip --require-hashes -r .audit-requirements.txt; \
	  status=$$?; rm -f .audit-requirements.txt; exit $$status

erd: ## Regenerate docs/diagram.md from the models
	$(UV) run python scripts/generate_erd.py

check-commits: ## Check commit messages on this branch against develop
	ci/check-commits.sh origin/develop..HEAD
