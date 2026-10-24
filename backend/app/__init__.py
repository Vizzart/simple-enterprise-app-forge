from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.celery_init import celery_init_app
from app.config import Config
from app.database import models  # noqa: F401  (registers all tables for Alembic)
from app.endpoints import auth
from app.extensions import api, db, migrate


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    app.json.sort_keys = False

    db.init_app(app)
    migrate.init_app(app, db)
    celery_init_app(app)
    CORS(app, expose_headers=["Content-Disposition"])

    api.init_app(app)
    api.add_namespace(auth.ns)

    @api.errorhandler(OperationalError)
    def handle_db_unavailable(error: OperationalError):
        db.session.rollback()
        return {"message": "Database connection error. Try again"}, 503

    @api.errorhandler(SQLAlchemyError)
    def handle_db_error(error: SQLAlchemyError):
        db.session.rollback()
        return {"message": "Database error occurred"}, 500

    return app
