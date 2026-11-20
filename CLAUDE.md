# SEAF — simple-enterprise-app-forge

Template for enterprise apps: Keycloak login (OIDC only, no local passwords) + full RBAC in the app DB (roles, permissions, functions, per-user overrides) out of the box, so new apps start with business logic. Auth/RBAC model and rules: `app-rbac` skill.

## Stack
- Python 3.14, Flask 3 (app factory), Flask-SQLAlchemy / SQLAlchemy 2, Flask-Migrate (Alembic)
- REST API: Flask-RESTX (Swagger UI at `/api/v1/docs`), Flask-CORS
- Background jobs: Celery + Redis (worker runs with embedded beat)
- PostgreSQL 18 via `psycopg` (v3)
- Auth: Keycloak 26 (OIDC); the API verifies Keycloak access tokens with PyJWT + JWKS (`app/auth/`)
- Local dev: the app stack in docker compose driven by `Makefile`; the infrastructure it needs (Keycloak, Vault, registry, GitLab) is a separate repo, `devops`

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
- `Makefile` — entry point for the app stack (`make help`)
- `docker-compose.yml` — app stack: `backend`, `worker`, `db`, `redis`; `backend` and `worker` join the external network `seaf-dev` (created by the infrastructure) to reach `keycloak:8080`
- Infrastructure is **not in this repo**: Keycloak + its Postgres, Vault, registry and GitLab are in the sibling repo `../devops` (`compose/`, compose project `seaf-infra`). Start it first with `make -C ../devops infrastructure`. The realm files are in `../devops/compose/keycloak/import/`: `seaf-realm.json` (this app: clients `seaf-frontend` / `seaf-api`, test users, audit events) and `infra-realm.json` (the tools). Notes about these tools: `../devops/docs/`
- `.claude/skills/` — project knowledge, committed: `app-rbac` (auth + RBAC model), `app-db-models` (model/migration conventions), `app-celery-tasks` (background jobs), `pm-board` (GitHub issues + kanban)
- `lab/` — Kubernetes course (theory, tasks, Vagrant VM in `lab/result/vm`); local only (git-ignored), not part of the app
- Personal notes (the Obsidian vault `wiki.seaf`) are a separate repo next to this one (`../wiki.seaf`); never put required project knowledge there or reference it

## Config
- Read config only via `os.environ` / `os.getenv` in `Config`; never hardcode secrets.
- Local dev: env files in `.envs/`. Ignored by git and Docker; only `.envs/*.example` templates are committed — keep them in sync.
- Inside compose, services reach each other by service name (`db`, `redis`, `keycloak`), not `localhost`.

Env vars:
- `.envs/.flask`: `FLASK_APP`, `DEBUG`, `PORT`, `SECRET_KEY`, `DATABASE_URL`, `API_VERSION`, `API_TITLE`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `KEYCLOAK_SWAGGER_CLIENT_ID`
- `.envs/.postgres`: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (names required by the official image)
- `.envs/.flask` (seed): `ADMIN_USERS` — JSON list of bootstrap admins (`keycloak_id`, `email`, `name`, `surname`) for `init_db()`
- `.envs/.flask` (seed, optional): `RBAC_SEED_FILE` — path to another RBAC seed YAML (default `app/database/seed/rbac.yaml`)
- `.envs/.flask` (Keycloak): `KEYCLOAK_ISSUER` (`http://localhost:8080/realms/seaf`, must equal token `iss`), `KEYCLOAK_JWKS_URL` (`http://keycloak:8080/realms/seaf/protocol/openid-connect/certs`, internal URL), `KEYCLOAK_AUDIENCE` (`seaf-api`)
- The env files of the infrastructure (`.keycloak`, `.keycloak-db`, `.gitlab`, `.vault-init.json`) are in `../devops/.envs/`

## Commands
- Infrastructure (Keycloak :8080, Vault :8200 starts sealed, registry :5001, GitLab :8929): `make -C ../devops infrastructure`, stop with `make -C ../devops infrastructure-down`. Everything about Keycloak, Vault, GitLab and the registry (reset, unseal, admin, adding people, logs) is in the devops repo: `make -C ../devops help`, `../devops/docs/`
- `make up` / `down` / `restart` / `logs` / `ps` — app stack (API on host :5050 — :5000 is taken by macOS AirPlay; Postgres on host :5432). `up` does not start the infrastructure, it checks that it is running (network `seaf-dev`)
- `make reset-db` — wipe the app DB (the infrastructure is untouched)
- Keycloak: admin console http://localhost:8080/admin (credentials in `../devops/.envs/.keycloak`); test users `anna`, `piotr`, `ewa`, `jan`, password `test`. The realm file is imported only when the realm does not exist: after editing `seaf-realm.json` run `make -C ../devops keycloak-reset` (wipes the Keycloak DB incl. users and audit events)
- Registry: `make registry-push` (backend + worker images → `localhost:5001/seaf/{backend,worker}:$(TAG)`, TAG defaults to `dev`; needs the registry from the infrastructure), `make -C ../devops registry-ls`; pull with `docker pull localhost:5001/<repo>:<tag>`
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
- Skills in `.claude/skills/` are prefixed by area: `pm-` (project management), `app-`. Infrastructure skills live in the devops repo.
