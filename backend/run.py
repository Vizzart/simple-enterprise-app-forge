
tak from app import create_app
from app.database.db import db_manager
from app.celery_init import import Celery

flask_app = create_app()
celery_app = flask_app.extensions['celery']
flask_app.app_context().push()


@flask_app.shell_context_processor
def make_shell_context():
    return dict(db=db_manager,
    )