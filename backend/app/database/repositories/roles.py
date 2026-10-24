"""Dostęp do danych ról (dim_role) i ich przypisań do użytkowników (map_role_user)."""

from app.database.models import Role, RoleUser, User
from app.database.repositories import users
from app.extensions import db


def get_roles() -> list[Role]:
    return db.session.query(Role).order_by(Role.role_name).all()


def get_role(role_name: str) -> Role | None:
    return db.session.query(Role).filter(Role.role_name == role_name).first()


def get_or_raise(role_name: str) -> Role:
    role = get_role(role_name)
    if role is None:
        raise ValueError(f"Role '{role_name}' does not exist")
    return role


def has_role(user: User | None, role_name: str) -> bool:
    """Czy AKTYWNY użytkownik ma rolę — nieaktywny nie ma żadnej."""
    if not users.is_active(user):
        return False
    return any(role.role_name == role_name for role in user.roles)


def add_role(user: User, role_name: str) -> None:
    """Nadaje rolę; ponowne nadanie tej samej roli nic nie zmienia."""
    role = get_or_raise(role_name)
    if any(link.role_id == role.id for link in user.role_links):
        return
    db.session.add(RoleUser(user=user, role=role))
    db.session.commit()


def remove_role(user: User, role_name: str) -> None:
    role = get_or_raise(role_name)
    for link in list(user.role_links):
        if link.role_id == role.id:
            db.session.delete(link)
    db.session.commit()
