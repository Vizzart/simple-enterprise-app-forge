"""Namespace `auth`: dane zalogowanego użytkownika.

Logowanie odbywa się w Keycloak (frontend / Swagger "Authorize"), nie w tym API.
"""

from flask_restx import Namespace, Resource

from app.auth import current_user, login_required
from app.docs import models
from app.rbac import access

ns = Namespace("auth", description="Current user — login happens in Keycloak")


@ns.route("/me")
class Me(Resource):
    @ns.doc("get_current_user")
    @ns.marshal_with(models.me)
    @ns.response(401, "Missing or invalid token", models.error)
    @ns.response(403, "User is inactive", models.error)
    @ns.response(503, "Keycloak is unavailable", models.error)
    @login_required
    def get(self):
        """Zalogowany użytkownik: profil, role, czy admin i dostępne funkcje.

        Pierwsze wywołanie zakłada użytkownika w bazie (just-in-time provisioning).
        """
        user = current_user()
        user.is_admin = access.user_is_admin(user)
        user.functions = access.allowed_functions(user)
        return user
