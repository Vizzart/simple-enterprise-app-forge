from app import create_app
from app.database import seed
from app.database.repositories import roles, users
from app.extensions import db
from app.rbac import access

flask_app = create_app()
celery_app = flask_app.extensions["celery"]


@flask_app.shell_context_processor
def make_shell_context():
    return {"db": db, "users": users, "roles": roles, "access": access, "seed": seed}
