"""Reguły dostępu RBAC: status użytkownika -> override -> reguła AND."""

from app.database.models import Function, User
from app.database.repositories import roles, users
from app.extensions import db

ADMIN_ROLE = "administrator"


def user_is_active(user: User | None) -> bool:
    return users.is_active(user)


def user_is_admin(user: User | None) -> bool:
    return roles.has_role(user, ADMIN_ROLE)


def user_can(user: User | None, function_code: str) -> bool:
    """Czy użytkownik może użyć funkcji `function_code`.

    1. nieaktywny (albo brak użytkownika) -> nie
    2. nieznana funkcja -> nie
    3. override w map_user_function_override -> decyduje `allow`
    4. reguła AND: uprawnienia z ról muszą zawierać WSZYSTKIE wymagane przez funkcję;
       funkcja bez wymaganych uprawnień -> nie
    """
    if not user_is_active(user):
        return False

    function = db.session.query(Function).filter(Function.code == function_code).first()
    if function is None:
        return False

    for override in user.function_overrides:
        if override.function_id == function.id:
            return override.allow

    required = {p.code for p in function.required_permissions}
    if not required:
        return False
    granted = {p.code for role in user.roles for p in role.permissions}
    return required <= granted


def allowed_functions(user: User | None) -> list[str]:
    """Kody wszystkich funkcji, których użytkownik może użyć (np. dla menu we frontendzie)."""
    if not user_is_active(user):
        return []
    codes = [code for (code,) in db.session.query(Function.code).order_by(Function.code)]
    return [code for code in codes if user_can(user, code)]
