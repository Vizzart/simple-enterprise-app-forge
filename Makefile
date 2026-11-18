# SEAF — local environment. Usage: make <target> [ENV=dev]
# ENV selects infra/$(ENV)/compose.yml; only `dev` exists.

ENV ?= dev

ifneq ($(ENV),dev)
$(error ENV=$(ENV) is not supported; only ENV=dev)
endif

APP   := docker compose -f docker-compose.yml
INFRA := docker compose -f infra/$(ENV)/compose.yml
KEYCLOAK_DB_VOLUME := seaf-$(ENV)-keycloak-db
VAULT_VOLUME := seaf-$(ENV)-vault
VAULT_KEYS := .envs/.vault-init.json
REGISTRY := localhost:5001
TAG ?= $(ENV)

.DEFAULT_GOAL := help
.PHONY: help infra-up infra-down infra-logs keycloak-reset vault-init vault-unseal vault-status \
        vault-config vault-reset registry-push registry-ls \
        gitlab-up gitlab-down gitlab-logs gitlab-admin \
        up down restart logs ps migrate reset-db lint

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- external infra (Keycloak, Vault, registry) — keep it running -----------------

infra-up: ## Start external infra (Keycloak + its DB, registry; GitLab: make gitlab-up)
	$(INFRA) up -d --wait

infra-down: ## Stop external infra incl. GitLab (data kept in volumes)
	$(INFRA) --profile gitlab down

infra-logs: ## Follow external infra logs
	$(INFRA) logs -f

keycloak-reset: ## Wipe Keycloak DB (users, sessions, audit!) and re-import seaf-realm.json
	$(INFRA) rm -sf keycloak keycloak-db
	docker volume rm -f $(KEYCLOAK_DB_VOLUME)
	$(INFRA) up -d --wait

vault-init: ## Initialize Vault once (1 key share) -> unseal key + root token in .envs/.vault-init.json
	@test ! -f $(VAULT_KEYS) || { echo "$(VAULT_KEYS) exists - already initialized (make vault-reset to start over)"; exit 1; }
	$(INFRA) exec -T vault vault operator init -key-shares=1 -key-threshold=1 -format=json > $(VAULT_KEYS)
	@chmod 600 $(VAULT_KEYS)
	@echo "saved $(VAULT_KEYS) (local dev only)"

vault-unseal: ## Unseal Vault with the saved key (needed after every restart) — http://localhost:8200
	@test -f $(VAULT_KEYS) || { echo "run make vault-init first"; exit 1; }
	$(INFRA) exec -T vault vault operator unseal "$$(python3 -c 'import json;print(json.load(open("$(VAULT_KEYS)"))["unseal_keys_b64"][0])')"

vault-status: ## Show Vault seal status
	-$(INFRA) exec vault vault status

vault-config: ## Configure Vault for Keycloak login (policies, OIDC role, group mapping); idempotent
	./infra/$(ENV)/vault/configure.sh

vault-reset: ## Wipe Vault data (secrets, policies, auth config!) — then make vault-init again
	$(INFRA) rm -sf vault
	docker volume rm -f $(VAULT_VOLUME)
	rm -f $(VAULT_KEYS)
	$(INFRA) up -d --wait vault

registry-push: infra-up ## Build the app images (backend, worker) and push them to the local registry (TAG=dev)
	REGISTRY=$(REGISTRY) TAG=$(TAG) $(APP) build backend worker
	REGISTRY=$(REGISTRY) TAG=$(TAG) $(APP) push backend worker

registry-ls: ## List repositories and tags in the local registry
	@for repo in $$(curl -s http://$(REGISTRY)/v2/_catalog | python3 -c 'import sys,json;print(" ".join(json.load(sys.stdin)["repositories"]))'); do \
		echo "$$repo: $$(curl -s http://$(REGISTRY)/v2/$$repo/tags/list | python3 -c 'import sys,json;print(" ".join(json.load(sys.stdin)["tags"] or []))')"; \
	done

gitlab-up: ## Start GitLab (first start takes several minutes), sign-up form off — http://localhost:8929
	$(INFRA) --profile gitlab up -d --wait gitlab
	$(INFRA) --profile gitlab exec -T gitlab gitlab-rails runner 'ApplicationSetting.current.update!(signup_enabled: false)'

gitlab-down: ## Stop GitLab only (data kept in volumes)
	$(INFRA) --profile gitlab stop gitlab

gitlab-logs: ## Follow GitLab logs
	$(INFRA) --profile gitlab logs -f gitlab

gitlab-admin: ## Make a GitLab user admin: make gitlab-admin EMAIL=you@gmail.com
	@test -n "$(EMAIL)" || { echo "usage: make gitlab-admin EMAIL=you@gmail.com"; exit 1; }
	$(INFRA) --profile gitlab exec gitlab gitlab-rails runner \
		'u = User.find_by_any_email("$(EMAIL)") or abort("no GitLab user with email $(EMAIL) — log in once first"); u.admin = true; u.save!; puts "#{u.username} is now admin"'

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