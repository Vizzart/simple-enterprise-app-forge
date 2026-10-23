from flask import Blueprint, current_app

main = Blueprint('main', __name__)


@main.app_context_processor
def inject_permissions():
    return dict(app_name=current_app.config['APP_NAME'])

