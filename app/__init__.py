from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from  .config  import config
db = SQLAlchemy()

migrate = Migrate()


def create_app(config_name):
    """

    :param config_name:
    :return:
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    migrate.init_app(app, db, render_as_batch=True, compare_type=True)


    return app