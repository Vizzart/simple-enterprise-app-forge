# SEAF : simple-enterprise-app-forge

A template for quickly building enterprise form-based applications. Login goes through **Keycloak** (OIDC, no local passwords) and the app ships a complete **RBAC** system (roles, permissions, functions, per-user overrides), so every new app starts with business logic, not authentication setup.

## Features

- **Keycloak login** — the API only verifies Keycloak access tokens (JWKS); users are created on first login. External logins (Google, Microsoft Entra ID) are added in Keycloak as identity providers, without app changes.
- **RBAC in the app database** — roles grant permissions, functions require permissions (a user needs **all** of them), per-user overrides, inactive users are always denied. Initial roles and permissions come from a YAML seed.
- **REST API with Swagger** — Flask-RESTX, "Authorize" in Swagger logs in through Keycloak.
- **Background jobs** — Celery + Redis.
- **Local infrastructure in a separate repo** — Keycloak (+ Postgres), Vault, the image registry and GitLab CE live in the `devops` repo and start with one command: `make -C ../devops infrastructure`.

## Stack

Python 3.14 · Flask 3 · Flask-RESTX · SQLAlchemy 2 / Flask-Migrate · PostgreSQL 18 · Celery + Redis · Keycloak 26 · PyJWT · Docker Compose

## Quick start

Requirements: Docker Desktop, `make`, Python 3.14 (for local tooling), and the `devops` repo next to this one (`../devops`).

```bash
# 1. the infrastructure (Keycloak, Vault, registry, GitLab; the first GitLab start takes several minutes).
#    First time: fill in ../devops/.envs (see the README there)
make -C ../devops infrastructure

# 2. env files of the app: copy templates and fill in values
for f in .envs/*.example; do cp -n "$f" "${f%.example}"; done

# 3. the app
make up

# 4. database: migrations + initial roles / admins
docker compose exec backend flask --app run db init      # first time only
docker compose exec backend flask --app run db migrate -m "initial"
docker compose exec backend flask --app run db upgrade
docker compose exec backend flask --app run shell         # >>> seed.init_db()
```

`make help` lists all commands of the app; `make -C ../devops help` lists the infrastructure ones.

## Local URLs

| Service | URL | Login |
|---|---|---|
| API + Swagger UI | http://localhost:5050/api/v1/docs | "Authorize" → `anna` / `piotr` / `ewa` / `jan`, password `test` |
| Keycloak admin (infrastructure) | http://localhost:8080/admin | `../devops/.envs/.keycloak` |
| Keycloak account (realm `seaf`) | http://localhost:8080/realms/seaf/account | test users above |
| Image registry (infrastructure) | http://localhost:5001/v2/_catalog | — |
| GitLab (infrastructure) | http://localhost:8929 | Keycloak realm `infra` → Google |

The API runs on host port **5050** because macOS uses 5000 for AirPlay.

## Project layout

```
backend/                 Flask app (Docker build context)
  app/auth/              Keycloak token verification, @login_required, @function_required
  app/rbac/              access rules (user_can, user_is_admin)
  app/database/          models, repositories, seed (rbac.yaml, init_db)
  app/endpoints/         REST API namespaces
.envs/*.example          env templates (real .envs/* files are git-ignored)
.claude/skills/          project knowledge for Claude Code (RBAC, DB models, Celery, PM board)
docker-compose.yml       app stack: backend, worker, db, redis
Makefile                 app commands (the infrastructure is in ../devops)
lab/                     Kubernetes course and labs (local only, git-ignored)
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
