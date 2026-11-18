# SEAF — simple-enterprise-app-forge

Template for enterprise apps: Keycloak login (OIDC only, no local passwords) + full RBAC in the app DB (roles, permissions, functions, per-user overrides) out of the box, so new apps start with business logic. Auth/RBAC model and rules: `app-rbac` skill.

## Stack
- Python 3.14, Flask 3 (app factory), Flask-SQLAlchemy / SQLAlchemy 2, Flask-Migrate (Alembic)
- REST API: Flask-RESTX (Swagger UI at `/api/v1/docs`), Flask-CORS
- Background jobs: Celery + Redis (worker runs with embedded beat)
- PostgreSQL 18 via `psycopg` (v3)
- Auth: Keycloak 26 (OIDC); the API verifies Keycloak access tokens with PyJWT + JWKS (`app/auth/`)
- Local dev: docker compose driven by `Makefile`

## Layout
Everything Python lives in `backend/` (Docker build context; run Python tooling from there).
- `backend/app/__init__.py` — `create_app(config)`, error handlers, API namespaces
- `backend/app/config.py` — `Config` class, values only from env vars
- `backend/app/extensions.py` — `db`, `migrate`, `api` instances (Swagger auth: Keycloak password flow + bearer)
- `backend/app/celery_init.py` — `celery_init_app(app)`, tasks run inside the app context
- `backend/app/database/models/` — SQLAlchemy models (schema only; diagram: `.claude/skills/app-rbac/`)
- `backend/app/database/repositories/` — data access functions per area (`users`, `roles`)
- `backend/app/database/seed/` — `rbac.yaml` (initial roles/permissions/functions) + `init_db()`
- `backend/app/rbac/access.py` — access rules (`user_can`, `user_is_admin`, ...)
- `backend/app/auth/` — Keycloak token verification (`tokens.py`), just-in-time user provisioning (`provisioning.py`), `@login_required` / `@function_required` / `current_user()` (`decorators.py`)
- `backend/app/endpoints/` — RESTX namespaces (`auth`: `GET /api/v1/auth/me`); `backend/app/docs/models.py` — Swagger models
- `backend/run.py` — entry point for `flask` and `celery -A run`
- `backend/app/requirements.txt` — pinned runtime deps; `requirements-dev.txt` adds ruff, mypy, pytest
- `backend/pyproject.toml` — config for ruff (lint + import sort + format), mypy, pytest
- `backend/local.Dockerfile` — dev image; `backend/Dockerfile` — production image
- `Makefile` — entry point for local dev (`make help`); `ENV` (default `dev`) selects `infra/$(ENV)/`
- `docker-compose.yml` — app stack: `backend`, `worker`, `db`, `redis`
- `infra/dev/compose.yml` — external dev infra, own lifecycle (project `seaf-infra`): `keycloak` + `keycloak-db`, `vault` (server mode, config in `infra/dev/vault/config/vault.hcl`), `registry` (registry:2), `gitlab` (compose profile `gitlab`, started only by `make gitlab-up`). Creates network `seaf-dev`; `backend` and `worker` join it to reach `keycloak:8080`
- `infra/dev/keycloak/import/seaf-realm.json` — realm `seaf` (the app): clients `seaf-frontend` / `seaf-api`, test users, audit events
- `infra/dev/keycloak/import/infra-realm.json` — realm `infra` (infra tools, separate from app users): Google identity provider, clients `gitlab` and `vault`, groups `devops` and `developers` (a `groups` mapper in each client puts them in the token claim `groups`). Secrets are `${ENV}` placeholders resolved by Keycloak at import from `.envs/.keycloak`. Do not add a `clientScopes` section: Keycloak then skips the standard scopes (`profile`, `email`, ...) and logins break
- `infra/dev/vault/` — `config/vault.hcl` (server), `policies/*.hcl` (`seaf-admin`, `seaf-developer`), `roles/keycloak.json` (OIDC login role), `configure.sh` (run by `make vault-config`: policies, OIDC login via Keycloak, Keycloak group → Vault policy: `devops` → `seaf-admin`, `developers` → `seaf-developer`)
- `.claude/skills/` — project knowledge, committed: `app-rbac` (auth + RBAC model), `app-db-models` (model/migration conventions), `app-celery-tasks` (background jobs), `pm-board` (GitHub issues + kanban), `devops-k8s-node-prep` (preparing Ubuntu nodes for kubeadm)
- `wiki.seaf/` — personal notes, an Obsidian vault with its own git repo; never put required project knowledge there or reference it

## Config
- Read config only via `os.environ` / `os.getenv` in `Config`; never hardcode secrets.
- Local dev: env files in `.envs/`. Ignored by git and Docker; only `.envs/*.example` templates are committed — keep them in sync.
- Inside compose, services reach each other by service name (`db`, `redis`, `keycloak`), not `localhost`.

Env vars:
- `.envs/.flask`: `FLASK_APP`, `DEBUG`, `PORT`, `SECRET_KEY`, `DATABASE_URL`, `API_VERSION`, `API_TITLE`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `KEYCLOAK_SWAGGER_CLIENT_ID`
- `.envs/.postgres`: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (names required by the official image)
- `.envs/.keycloak`: `KC_BOOTSTRAP_ADMIN_USERNAME`, `KC_BOOTSTRAP_ADMIN_PASSWORD`, `KC_DB_USERNAME`, `KC_DB_PASSWORD`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITLAB_OIDC_CLIENT_SECRET`, `VAULT_OIDC_CLIENT_SECRET`
- `.envs/.gitlab`: `GITLAB_ROOT_PASSWORD`, `GITLAB_OIDC_CLIENT_SECRET` (same value as in `.envs/.keycloak`)
- `.envs/.flask` (seed): `ADMIN_USERS` — JSON list of bootstrap admins (`keycloak_id`, `email`, `name`, `surname`) for `init_db()`
- `.envs/.flask` (seed, optional): `RBAC_SEED_FILE` — path to another RBAC seed YAML (default `app/database/seed/rbac.yaml`)
- `.envs/.keycloak-db`: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (same credentials as `KC_DB_*`)
- `.envs/.flask` (Keycloak): `KEYCLOAK_ISSUER` (`http://localhost:8080/realms/seaf`, must equal token `iss`), `KEYCLOAK_JWKS_URL` (`http://keycloak:8080/realms/seaf/protocol/openid-connect/certs`, internal URL), `KEYCLOAK_AUDIENCE` (`seaf-api`)

## Commands
- `make infra-up` — Keycloak (:8080) + registry (:5001); keep running. `make infra-down` stops it, data stays in volumes `seaf-dev-keycloak-db`, `seaf-dev-registry`
- `make up` / `down` / `restart` / `logs` / `ps` — app stack (API on host :5050 — :5000 is taken by macOS AirPlay; Postgres on host :5432); `up` starts infra first
- `make reset-db` — wipe the app DB (Keycloak untouched)
- Keycloak: admin console http://localhost:8080/admin (`.envs/.keycloak`); test users `anna`, `piotr`, `ewa`, `jan`, password `test`. The realm file is imported only when the realm does not exist: after editing `seaf-realm.json` run `make keycloak-reset` (wipes Keycloak DB incl. users and audit events)
- Vault: http://localhost:8200 (UI + API), started by `make infra-up` but **sealed**. First time `make vault-init` (unseal key + root token → `.envs/.vault-init.json`, git-ignored), then `make vault-unseal` after every restart; `make vault-status`; `make vault-reset` wipes it. After init + unseal run `make vault-config` (policies, OIDC login through Keycloak, group → policy mapping; safe to repeat). The KV v2 engine `seaf/` is created by hand (`vault secrets enable -path=seaf kv-v2`). To add a group: Keycloak group in `infra-realm.json` + a pair in `GROUP_POLICIES` in `configure.sh` + `make vault-config`
- GitLab: `make gitlab-up` (several minutes) → http://localhost:8929, login redirects to Keycloak realm `infra` → Google. `root` login (password in `.envs/.gitlab`): http://localhost:8929/users/sign_in?auto_sign_in=false. `make gitlab-admin EMAIL=...` grants admin after the first Google login (GitLab CE cannot make admins from a Keycloak group — Premium feature). Accounts are created only at the first login of a person that exists in Keycloak; `make gitlab-up` switches the sign-up form off and a login with a new Keycloak user id (e.g. after `make keycloak-reset`) is linked to the GitLab account with the same email. `make gitlab-down` stops it
- Adding a person to the infra tools: their Google email to *Test users* in Google Cloud → they log in once at http://localhost:8080/realms/infra/account → add them to the Keycloak group (`devops` or `developers`) in realm `infra` (admin console). Nothing is created by hand in GitLab or Vault. `make keycloak-reset` wipes users and their group membership (new user ids): everything that must survive belongs in the realm file
- Registry: `make registry-push` (backend + worker images → `localhost:5001/seaf/{backend,worker}:$(TAG)`, TAG defaults to `ENV`), `make registry-ls`; pull with `docker pull localhost:5001/<repo>:<tag>`
- Migrations: `make migrate`; new migration: `docker compose exec backend flask db migrate -m "..."`
- Dev tools (from `backend/`, after `pip install -r app/requirements-dev.txt`):
  - `ruff check .` — lint (`--fix` auto-fixes, incl. import order)
  - `ruff format .` — format code
  - `mypy app` — type check
  - `pytest` — tests in `backend/tests/`

## Conventions
- New features go in RESTX namespaces registered in `create_app`.
- Protect endpoints with `@login_required` or `@function_required("<function code>")` from `app.auth`; never parse tokens or check roles inline. Function codes must exist in `app/database/seed/rbac.yaml`.
- Document responses with Swagger models from `app/docs/models.py` (`@ns.marshal_with`, `@ns.response`).
- DB: `snake_case` singular table names, `dim_` for entities, `map_` for join tables; full rules in `.claude/skills/app-db-models/SKILL.md`.
- Code must pass `ruff check`, `ruff format --check` and `mypy` (config in `pyproject.toml`, line length 100); run them after changes.
- Commits: Conventional Commits in English (`feat:`, `fix:`, `chore:`).
- Tasks live in GitHub Issues + Project #4 — use the `pm-board` skill.
- Skills in `.claude/skills/` are prefixed by area: `pm-` (project management), `app-`, `devops-`.
