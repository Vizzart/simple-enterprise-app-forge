import os

from flask_jwt_extended import JWTManager


from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

jwt = JWTManager()
db = SQLAlchemy()
migrate = Migrate()

autorization = {
    "jwt": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "Bearer token"
    }
}

api = Api(
    version=os.getenv("API_VERSION"),
    title=os.getenv("API_TITLE"),
    authorizations=autorization,
    prefix="/api/v1",
    doc="api/",
)

