import os

from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

_keycloak_issuer = os.getenv("KEYCLOAK_ISSUER", "http://localhost:8080/realms/seaf")

# Swagger "Authorize": log in at Keycloak (username + password) or paste a token
authorizations = {
    "keycloak": {
        "type": "oauth2",
        "flow": "password",
        "tokenUrl": f"{_keycloak_issuer}/protocol/openid-connect/token",
        "scopes": {},
    },
    "bearer": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "Keycloak access token: `Bearer <token>`",
    },
}

api = Api(
    version=os.getenv("API_VERSION", "0.1.0"),
    title=os.getenv("API_TITLE", "SEAF API"),
    description="Login happens in Keycloak; the API only verifies Keycloak access tokens.",
    authorizations=authorizations,
    security=["keycloak", "bearer"],
    prefix="/api/v1",
    doc="/api/v1/docs",
)
