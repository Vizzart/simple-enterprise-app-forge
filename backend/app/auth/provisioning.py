"""Just-in-time provisioning: użytkownik z tokenu Keycloak -> rekord w dim_user."""

from app.database.models import User
from app.database.repositories import users


def sync_user(claims: dict) -> User:
    """Zakłada użytkownika przy pierwszym logowaniu, przy kolejnych odświeża dane z tokenu.

    Szuka po `sub` (keycloak_id), także wśród nieaktywnych — nigdy po e-mailu.
    Statusu nie zmienia: nieaktywny zostaje nieaktywny.
    """
    profile = {
        "email": claims.get("email", ""),
        "name": claims.get("given_name", ""),
        "surname": claims.get("family_name", ""),
        "identity_provider": claims.get("identity_provider", "keycloak"),
    }
    user = users.get_by_keycloak_id(claims["sub"], include_inactive=True)
    if user is None:
        return users.create(keycloak_id=claims["sub"], **profile)

    changed = {key: value for key, value in profile.items() if getattr(user, key) != value}
    if changed:
        users.update(user, **changed)
    return user
