import json
import os


def _bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    DEBUG: bool = _bool("DEBUG")
    APP = os.environ.get("FLASK_APP")
    PORT: int = int(os.environ.get("PORT", 5000))
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 10,
        "pool_recycle": 30,
        "pool_pre_ping": True,
    }

    # Keycloak token verification: ISSUER must equal the token `iss`,
    # JWKS_URL is the URL reachable from the backend (inside compose: http://keycloak:8080/...)
    KEYCLOAK_ISSUER = os.environ.get("KEYCLOAK_ISSUER")
    KEYCLOAK_JWKS_URL = os.environ.get("KEYCLOAK_JWKS_URL")
    KEYCLOAK_AUDIENCE = os.environ.get("KEYCLOAK_AUDIENCE", "seaf-api")
    # Swagger "Authorize" logs in at Keycloak with this public client
    SWAGGER_UI_OAUTH_CLIENT_ID = os.environ.get("KEYCLOAK_SWAGGER_CLIENT_ID", "seaf-frontend")

    # bootstrap admins for init_db(), JSON list of
    # {"keycloak_id": "...", "email": "...", "name": "...", "surname": "..."}
    ADMIN_USERS: list[dict] = json.loads(os.environ.get("ADMIN_USERS", "[]"))
    # RBAC seed for init_db(); default: app/database/seed/rbac.yaml
    RBAC_SEED_FILE = os.environ.get("RBAC_SEED_FILE")

    CELERY = {
        "broker_url": os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
        "result_backend": os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
        "task_ignore_result": True,
        "worker_cancel_long_running_tasks_on_connection_loss": True,
    }
