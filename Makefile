# SEAF — local environment. Usage: make <target> [ENV=dev]
# ENV selects infra/$(ENV)/compose.yml; only `dev` exists.

ENV ?= dev

ifneq ($(ENV),dev)
$(error ENV=$(ENV) is not supported; only ENV=dev)
endif

APP   := docker compose -f docker-compose.yml
INFRA := docker compose -f infra/$(ENV)/compose.yml
KEYCLOAK_DB_VOLUME := seaf-$(ENV)-keycloak-db
REGISTRY := localhost:5001
TAG ?= $(ENV)

.DEFAULT_GOAL := help
.PHONY: help infra-up infra-down infra-logs keycloak-reset registry-push registry-ls \
        up down restart logs ps migrate reset-db lint

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- external infra (Keycloak, registry) — keep it running -----------------

infra-up: ## Start external infra (Keycloak + its DB, registry) and wait until healthy
	$(INFRA) up -d --wait

infra-down: ## Stop external infra (data kept in volumes)
	$(INFRA) down

infra-logs: ## Follow external infra logs
	$(INFRA) logs -f

keycloak-reset: ## Wipe Keycloak DB (users, sessions, audit!) and re-import seaf-realm.json
	$(INFRA) rm -sf keycloak keycloak-db
	docker volume rm -f $(KEYCLOAK_DB_VOLUME)
	$(INFRA) up -d --wait

registry-push: ## Build the backend image and push it to the local registry (TAG=dev)
	docker build -t $(REGISTRY)/seaf/backend:$(TAG) -f backend/local.Dockerfile backend
	docker push $(REGISTRY)/seaf/backend:$(TAG)

registry-ls: ## List repositories and tags in the local registry
	@for repo in $$(curl -s http://$(REGISTRY)/v2/_catalog | python3 -c 'import sys,json;print(" ".join(json.load(sys.stdin)["repositories"]))'); do \
		echo "$$repo: $$(curl -s http://$(REGISTRY)/v2/$$repo/tags/list | python3 -c 'import sys,json;print(" ".join(json.load(sys.stdin)["tags"] or []))')"; \
	done

# --- application stack (backend, worker, db, redis) -------------------------

up: infra-up ## Start the app (starts infra first if needed)
	$(APP) up -d --build

down: ## Stop the app (infra keeps running)
	$(APP) down

restart: ## Restart backend and worker (worker does not auto-reload)
	$(APP) restart backend worker

logs: ## Follow app logs
	$(APP) logs -f

ps: ## Show app and infra containers
	@$(INFRA) ps
	@$(APP) ps

migrate: ## Apply DB migrations
	$(APP) exec backend flask db upgrade

reset-db: ## Wipe the app DB volume (Keycloak untouched)
	$(APP) down -v

# --- code quality -----------------------------------------------------------

lint: ## ruff + mypy (run in backend/, local venv)
	cd backend && ruff check . && ruff format --check . && mypy app