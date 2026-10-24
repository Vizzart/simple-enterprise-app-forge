from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)

from flask_restx import Namespace, Resource
#TODO
#keycloack

from marshmallow import ValidationError

from app.config import Config
from app.database.db import db_manager
from app.docs.models import login


ns = Namespace("auth")


def create_access_and_refresh_token(email: str) -> Tuple[str, str]:
    access = create_access_token(identity=email)
    refresh = create_refresh_token(
        identity=email,
        expires_delta=timedelta(hours=Config.JWT_REFRESH_EXPIRES)
    )
    return access, refresh


@ns.response(200, "Success")
@ns.response(401, "Unauthorized")
@ns.response(400, "Bad Request")
@ns.response(403, "Forbidden")
@ns.response(404, "Not Found")
@ns.response(500, "Internal Server Error")
@ns.route("/login")
class Login(Resource):
    return 200

