"""Modele Swaggera (flask-restx): opis odpowiedzi API i formatowanie (marshal_with)."""

from flask_restx import fields

from app.extensions import api

error = api.model(
    "Error",
    {"message": fields.String(description="Error description", example="Missing bearer token")},
)

user = api.model(
    "User",
    {
        "id": fields.Integer(readonly=True, example=1),
        "keycloak_id": fields.String(description="Keycloak `sub`", example="8a076bc0-..."),
        "email": fields.String(example="ewa@seaf.local"),
        "name": fields.String(example="Ewa"),
        "surname": fields.String(example="Wiśniewska"),
        "status": fields.String(enum=["active", "inactive"], example="active"),
        "identity_provider": fields.String(example="keycloak"),
        "roles": fields.List(
            fields.String,
            attribute=lambda u: sorted(role.role_name for role in u.roles),
            example=["viewer"],
        ),
    },
)

me = api.inherit(
    "Me",
    user,
    {
        "is_admin": fields.Boolean(example=False),
        "functions": fields.List(
            fields.String,
            description="Function codes the user can use (AND rule + overrides)",
            example=["roles.list", "users.list"],
        ),
    },
)
