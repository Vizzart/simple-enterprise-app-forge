# SEAF — local app environment. Usage: make <target>
#
# This repo is only the app (backend, worker, db, redis). The infrastructure it needs — Keycloak (login),
# Vault, the image registry and GitLab — lives in the devops repo and has its own lifecycle:
#
#   make -C ../devops infrastructure      # start it first and keep it running
#
# `make up` here does not start it, it only checks that it is running (network seaf-dev exists).

DEVOPS ?= ../devops
APP   := docker compose -f docker-compose.yml
REGISTRY := localhost:5001
TAG ?= dev

.DEFAULT_GOAL := help
.PHONY: help check-infrastructure up down restart logs ps migrate reset-db registry-push lint

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

check-infrastructure:
	@docker network inspect seaf-dev >/dev/null 2>&1 || { echo "The infrastructure is not running (network seaf-dev not found). Start it first: make -C $(DEVOPS) infrastructure"; exit 1; }

# --- application stack (backend, worker, db, redis) -------------------------

up: check-infrastructure ## Start the app (the infrastructure must run: make -C ../devops infrastructure)
	$(APP) up -d --build

down: ## Stop the app (the infrastructure keeps running)
	$(APP) down

restart: ## Restart backend and worker (worker does not auto-reload)
	$(APP) restart backend worker

logs: ## Follow app logs
	$(APP) logs -f

ps: ## Show the app containers
	@$(APP) ps

migrate: ## Apply DB migrations
	$(APP) exec backend flask db upgrade

reset-db: ## Wipe the app DB volume (the infrastructure is untouched)
	$(APP) down -v

registry-push: ## Build the app images (backend, worker) and push them to the local registry (TAG=dev; needs the registry from the infrastructure)
	@curl -sf http://$(REGISTRY)/v2/ >/dev/null || { echo "Registry $(REGISTRY) is not reachable. Start the infrastructure first: make -C $(DEVOPS) infrastructure"; exit 1; }
	REGISTRY=$(REGISTRY) TAG=$(TAG) $(APP) build backend worker
	REGISTRY=$(REGISTRY) TAG=$(TAG) $(APP) push backend worker

# --- code quality -----------------------------------------------------------

lint: ## ruff + mypy (run in backend/, local venv)
	cd backend && ruff check . && ruff format --check . && mypy app
