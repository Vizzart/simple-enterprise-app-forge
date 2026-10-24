# SEAF : simple-enterprise-app-forge

A template for quickly building enterprise form-based applications. Login goes through **Keycloak** (OIDC, no local passwords) and the app ships a complete **RBAC** system (roles, permissions, functions, per-user overrides), so every new app starts with business logic, not authentication setup.

## Features

- **Keycloak login** — the API only verifies Keycloak access tokens (JWKS); users are created on first login. External logins (Google, Microsoft Entra ID) are added in Keycloak as identity providers, without app changes.
- **RBAC in the app database** — roles grant permissions, functions require permissions (a user needs **all** of them), per-user overrides, inactive users are always denied. Initial roles and permissions come from a YAML seed.
- **REST API with Swagger** — Flask-RESTX, "Authorize" in Swagger logs in through Keycloak.
- **Background jobs** — Celery + Redis.
- **Local dev infra** — Keycloak (+ Postgres), image registry, GitLab CE with login through Keycloak → Google, all in Docker Compose and driven by a `Makefile`.

## Stack

Python 3.14 · Flask 3 · Flask-RESTX · SQLAlchemy 2 / Flask-Migrate · PostgreSQL 18 · Celery + Redis · Keycloak 26 · PyJWT · Docker Compose

## Quick start

Requirements: Docker Desktop, `make`, Python 3.14 (for local tooling).

```bash
# 1. env files: copy templates and fill in values
for f in .envs/*.example; do cp -n "$f" "${f%.example}"; done

# 2. infra (Keycloak, registry) and the app
make infra-up
make up

# 3. database: migrations + initial roles / admins
docker compose exec backend flask --app run db init      # first time only
docker compose exec backend flask --app run db migrate -m "initial"
docker compose exec backend flask --app run db upgrade
docker compose exec backend flask --app run shell         # >>> seed.init_db()
```

`make help` lists all commands.

## Local URLs

| Service | URL | Login |
|---|---|---|
| API + Swagger UI | http://localhost:5050/api/v1/docs | "Authorize" → `anna` / `piotr` / `ewa` / `jan`, password `test` |
| Keycloak admin | http://localhost:8080/admin | `.envs/.keycloak` |
| Keycloak account (realm `seaf`) | http://localhost:8080/realms/seaf/account | test users above |
| Image registry | http://localhost:5001/v2/_catalog | — |
| GitLab (`make gitlab-up`) | http://localhost:8929 | Keycloak realm `infra` → Google; `make gitlab-admin EMAIL=...` |

The API runs on host port **5050** because macOS uses 5000 for AirPlay.

## Project layout

```
backend/                 Flask app (Docker build context)
  app/auth/              Keycloak token verification, @login_required, @function_required
  app/rbac/              access rules (user_can, user_is_admin)
  app/database/          models, repositories, seed (rbac.yaml, init_db)
  app/endpoints/         REST API namespaces
infra/dev/               local infra: compose + Keycloak realm imports
.envs/*.example          env templates (real .envs/* files are git-ignored)
.claude/skills/          project knowledge for Claude Code (RBAC, DB models, Celery, PM board)
docker-compose.yml       app stack: backend, worker, db, redis
Makefile                 local environment commands
```

Detailed conventions, env variables and commands: [CLAUDE.md](CLAUDE.md).

## Development

```bash
cd backend
pip install -r app/requirements-dev.txt
ruff check . && ruff format --check . && mypy app && pytest
```

Commits follow Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`). Tasks are tracked in GitHub Issues and the project board.

## License

MIT — see [LICENSE](LICENSE).
