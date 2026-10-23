# SEAF — simple-enterprise-app-forge

Template for enterprise form-based web apps: local DB login + full RBAC (roles, permissions, assignments) out of the box, so new apps start with business logic.

## Stack
- Python 3.14, Flask 3 (app factory), Flask-SQLAlchemy / SQLAlchemy 2, Flask-Migrate (Alembic)
- Flask-Login (auth), Flask-WTF (forms + CSRF), Flask-APScheduler
- PostgreSQL via `psycopg` (v3)
- Production: gunicorn in Docker (`Dockerfile`)

## Layout
- `app/__init__.py` — `create_app(config_name)`, extensions (`db`, `migrate`)
- `app/config.py` — config classes, selected by `FLASK_CONFIG` (`dev`, `default`)
- `app/flasky.py` — app entry point (`app.flasky:app`)
- `app/models/` — SQLAlchemy models
- `app/requirements.txt` — pinned dependencies

## Config
- Locally, env vars come from `.env` (loaded by `load_dotenv()`).
- In k8s, env vars are injected from Vault; `load_dotenv()` does not override existing env vars, so they take precedence. Keep reading config only via `os.getenv`.
- `*.env` files are excluded by `.gitignore` and `.dockerignore` — never commit secrets or hardcode them in code.

## Commands
- Run locally: `flask --app app/flasky.py run`
- Migrations: `flask --app app/flasky.py db migrate -m "..."` then `db upgrade`
- Docker: `docker build -t seaf . && docker run -p 8000:8000 seaf`

## Conventions
- New features go in blueprints registered in `create_app`.
- Commits: Conventional Commits in English (`feat:`, `fix:`, `chore:`).
- Tasks live in GitHub Issues + Project #4 — use the `pm-board` skill.
- Skills in `.claude/skills/` are prefixed by area: `pm-` (project management), `app-`, `devops-`.
