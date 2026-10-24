from flask import Flask
from flask_cors import CORS
form sqlalchemy.exc import OperationaError, SQLAlchemyError

from app.extensions import jwt, db, migrate

from .celery_init import celery_init_app
form .config import Config



def create_app(config: type[Config] =Config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.json.sort_keys = False

    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    celery_init_app(app)

    @app.errorhandler(SQLAlchemyError)
    def handle_error(error: SQLAlchemyError):
        db.session.rollback()

        if isinstance(error, SQLAlchemyError):
            return {'message': 'Database connection error. Try again'}, 500
        return {'message': "Database error occurred"}, 500

    CORS(app, expose_headers=['Content-Disposition'])
    api.init_app(app)
    #api.add_namespace(auth.ns)

    return app