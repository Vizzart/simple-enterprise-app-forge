"""Inicjalizacja danych: zestawy RBAC z pliku YAML i administratorzy z ADMIN_USERS.

Wszystko idempotentne: uruchomione ponownie dopisuje tylko brakujące rekordy,
niczego nie usuwa i nie nadpisuje zmian zrobionych w bazie.
"""

from pathlib import Path

import yaml
from flask import current_app

from app.database.models import (
    Function,
    Permission,
    PermissionFunction,
    Role,
    RolePermission,
    RoleUser,
    User,
)
from app.database.repositories import roles, users
from app.extensions import db
from app.rbac.access import ADMIN_ROLE

DEFAULT_SEED_FILE = Path(__file__).with_name("rbac.yaml")


def init_db() -> None:
    """Dane startowe: role z uprawnieniami i funkcjami, potem administratorzy."""
    insert_roles()
    insert_admins()


def load_rbac_seed(path: str | Path | None = None) -> dict:
    """Wczytuje i sprawdza plik YAML. Błąd = ValueError z listą wszystkich problemów."""
    if path is None:
        path = current_app.config.get("RBAC_SEED_FILE") or DEFAULT_SEED_FILE
    with open(path, encoding="utf-8") as file:
        seed = yaml.safe_load(file) or {}

    seed = {
        "permissions": seed.get("permissions") or {},
        "functions": seed.get("functions") or {},
        "roles": seed.get("roles") or {},
    }
    known = set(seed["permissions"])
    errors = []
    for code, spec in seed["functions"].items():
        if not (spec or {}).get("requires"):
            errors.append(f"function '{code}': 'requires' is empty")
        for permission in (spec or {}).get("requires", []):
            if permission not in known:
                errors.append(f"function '{code}': unknown permission '{permission}'")
    for name, spec in seed["roles"].items():
        for permission in (spec or {}).get("permissions", []):
            if permission not in known:
                errors.append(f"role '{name}': unknown permission '{permission}'")
    if errors:
        raise ValueError(f"Invalid RBAC seed {path}:\n  " + "\n  ".join(errors))
    return seed


def insert_roles(seed: dict | None = None) -> None:
    """Wgrywa uprawnienia, funkcje (z wymaganymi uprawnieniami) i role (z uprawnieniami)."""
    if seed is None:
        seed = load_rbac_seed()
    permissions = _seed_permissions(seed["permissions"])
    _seed_functions(seed["functions"], permissions)
    _seed_roles(seed["roles"], permissions)
    db.session.commit()


def insert_admins(admins: list[dict] | None = None) -> None:
    """Zakłada administratorów (ADMIN_USERS) i nadaje im rolę ADMIN_ROLE.

    Istniejącego użytkownika (po keycloak_id) nie nadpisuje i nie aktywuje,
    tylko dopisuje brakującą rolę. Wymaga wcześniejszego insert_roles().
    """
    if admins is None:
        admins = current_app.config.get("ADMIN_USERS", [])
    role = roles.get_or_raise(ADMIN_ROLE)
    for admin in admins:
        user = users.get_by_keycloak_id(admin["keycloak_id"], include_inactive=True)
        if user is None:
            user = User(
                keycloak_id=admin["keycloak_id"],
                email=admin["email"],
                name=admin["name"],
                surname=admin["surname"],
            )
            db.session.add(user)
        if not any(link.role_id == role.id for link in user.role_links):
            db.session.add(RoleUser(user=user, role=role))
    db.session.commit()


def _seed_permissions(spec: dict[str, str]) -> dict[str, Permission]:
    permissions = {p.code: p for p in db.session.query(Permission).all()}
    for code, description in spec.items():
        if code not in permissions:
            permissions[code] = Permission(code=code, description=description)
            db.session.add(permissions[code])
    return permissions


def _seed_functions(spec: dict[str, dict], permissions: dict[str, Permission]) -> None:
    functions = {f.code: f for f in db.session.query(Function).all()}
    for code, function_spec in spec.items():
        function = functions.get(code)
        if function is None:
            function = Function(code=code, description=function_spec.get("description"))
            db.session.add(function)
        linked = {link.permission.code for link in function.permission_links}
        for permission_code in set(function_spec["requires"]) - linked:
            permission = permissions[permission_code]
            db.session.add(PermissionFunction(function=function, permission=permission))


def _seed_roles(spec: dict[str, dict], permissions: dict[str, Permission]) -> None:
    existing = {r.role_name: r for r in db.session.query(Role).all()}
    for role_name, role_spec in spec.items():
        role = existing.get(role_name)
        if role is None:
            role = Role(role_name=role_name)
            db.session.add(role)
        linked = {link.permission.code for link in role.permission_links}
        for permission_code in set((role_spec or {}).get("permissions", [])) - linked:
            db.session.add(RolePermission(role=role, permission=permissions[permission_code]))
