"""Dostęp do danych użytkowników (dim_user).

Każde zapytanie zwraca domyślnie tylko aktywnych użytkowników;
nieaktywnych trzeba poprosić jawnie: include_inactive=True.
"""

from sqlalchemy import func

from app.database.models import Role, RoleUser, User, UserStatus
from app.extensions import db

UPDATABLE_FIELDS = {"email", "name", "surname", "identity_provider", "status"}


def is_active(user: User | None) -> bool:
    return user is not None and user.status == UserStatus.ACTIVE


def _query(include_inactive: bool = False):
    query = db.session.query(User)
    if not include_inactive:
        query = query.filter(User.status == UserStatus.ACTIVE)
    return query


def get_users(include_inactive: bool = False) -> list[User]:
    return _query(include_inactive).order_by(User.surname, User.name).all()


def get_by_id(user_id: int, include_inactive: bool = False) -> User | None:
    return _query(include_inactive).filter(User.id == user_id).first()


def get_by_email(email: str, include_inactive: bool = False) -> User | None:
    return _query(include_inactive).filter(User.email == email).first()


def get_by_keycloak_id(keycloak_id: str, include_inactive: bool = False) -> User | None:
    return _query(include_inactive).filter(User.keycloak_id == keycloak_id).first()


def get_by_role(role_name: str, include_inactive: bool = False) -> list[User]:
    return (
        _query(include_inactive)
        .join(RoleUser, RoleUser.user_id == User.id)
        .join(Role, Role.id == RoleUser.role_id)
        .filter(Role.role_name == role_name)
        .order_by(User.surname, User.name)
        .all()
    )


def with_multiple_roles(include_inactive: bool = False) -> list[User]:
    """Użytkownicy z więcej niż jedną rolą."""
    return (
        _query(include_inactive)
        .join(RoleUser, RoleUser.user_id == User.id)
        .group_by(User.id)
        .having(func.count(RoleUser.role_id) > 1)
        .order_by(User.surname, User.name)
        .all()
    )


def create(
    keycloak_id: str,
    email: str,
    name: str,
    surname: str,
    identity_provider: str | None = None,
) -> User:
    """Nowy, aktywny użytkownik bez ról — role nadaje roles.add_role()."""
    user = User(
        keycloak_id=keycloak_id,
        email=email,
        name=name,
        surname=surname,
        identity_provider=identity_provider,
    )
    db.session.add(user)
    db.session.commit()
    return user


def update(user: User, **fields) -> User:
    """Zmienia tylko pola z UPDATABLE_FIELDS (keycloak_id i id są niezmienne)."""
    unknown = set(fields) - UPDATABLE_FIELDS
    if unknown:
        raise ValueError(f"Cannot update fields: {', '.join(sorted(unknown))}")
    for key, value in fields.items():
        setattr(user, key, value)
    db.session.commit()
    return user
