# SwarmOps — developer entrypoints. Run from the repo root.
# Backend lives in apps/api (Python venv), frontend in apps/web (npm).

API_DIR := apps/api
WEB_DIR := apps/web
VENV    := $(API_DIR)/.venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Setup ---------------------------------------------------------------
.PHONY: install install-api install-web
install: install-api install-web ## Install backend + frontend dependencies

install-api: ## Create venv and install the API (with dev extras)
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "$(API_DIR)[dev]"

install-web: ## Install frontend dependencies
	cd $(WEB_DIR) && npm install

# --- Run -----------------------------------------------------------------
.PHONY: dev dev-api dev-web
dev: ## Run API (:8080) and Web (:3000) together
	@echo "Starting SwarmOps API on :8080 and Web on :3000 ..."
	@$(MAKE) -j2 dev-api dev-web

dev-api: ## Run the FastAPI backend with reload
	cd $(API_DIR) && .venv/bin/uvicorn app.main:app --reload --port 8080

dev-web: ## Run the Next.js frontend
	cd $(WEB_DIR) && npm run dev

# --- Quality -------------------------------------------------------------
.PHONY: test test-api test-web
test: test-api ## Run the full test suite (backend; frontend added later)

test-api: ## Run backend tests
	cd $(API_DIR) && .venv/bin/pytest

.PHONY: lint lint-api lint-web
lint: lint-api lint-web ## Lint + typecheck backend and frontend

lint-api: ## ruff + mypy on the backend
	cd $(API_DIR) && .venv/bin/ruff check . && .venv/bin/mypy app

lint-web: ## eslint + tsc on the frontend
	cd $(WEB_DIR) && npm run lint && npm run typecheck

# --- Docker --------------------------------------------------------------
.PHONY: up down
up: ## Start the full stack via docker-compose
	docker compose up --build

down: ## Stop the docker-compose stack
	docker compose down
