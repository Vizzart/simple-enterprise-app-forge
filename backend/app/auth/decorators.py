"""Dekoratory endpointów: wymagają tokenu Keycloak i (opcjonalnie) dostępu do funkcji RBAC."""

from functools import wraps

from flask import g, request
from flask_restx import abort

from app.auth.provisioning import sync_user
from app.auth.tokens import InvalidToken, KeycloakUnavailable, verify_token
from app.database.models import User
from app.rbac import access


def current_user() -> User:
    """Zalogowany użytkownik bieżącego żądania (ustawiany przez login_required)."""
    return g.current_user


def login_required(view):
    """401 bez ważnego tokenu, 403 dla nieaktywnego użytkownika; ustawia current_user()."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            abort(401, "Missing bearer token")
        try:
            claims = verify_token(token.strip())
        except KeycloakUnavailable:
            abort(503, "Keycloak is unavailable")
        except InvalidToken as error:
            abort(401, f"Invalid token: {error}")

        user = sync_user(claims)
        if not access.user_is_active(user):
            abort(403, "User is inactive")
        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def function_required(function_code: str):
    """login_required + 403, jeśli użytkownik nie ma dostępu do funkcji (reguła AND / override)."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if not access.user_can(current_user(), function_code):
                abort(403, f"No access to function '{function_code}'")
            return view(*args, **kwargs)

        return wrapper

    return decorator
