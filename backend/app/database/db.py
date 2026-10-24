from flask import current_app
from sqlalchemy import func

from app.database.models import (
    Function,
    Permission,
    PermissionFunction,
    Role,
    RolePermission,
    RoleUser,
    User,
    UserStatus,
)
from app.extensions import db

ADMIN_ROLE = "administrator"

# Zestawy startowe dla insert_roles(). Funkcja wymaga WSZYSTKICH swoich uprawnień (reguła AND);
# rola dostaje uprawnienia, nigdy funkcje.
PERMISSIONS = {
    "user.read": "Podgląd użytkowników",
    "user.manage": "Zakładanie i edycja użytkowników",
    "role.read": "Podgląd ról i uprawnień",
    "role.manage": "Nadawanie i odbieranie ról",
}

FUNCTIONS = {
    "users.list": ("Lista użytkowników", ["user.read"]),
    "users.edit": ("Edycja użytkownika", ["user.read", "user.manage"]),
    "roles.list": ("Lista ról", ["role.read"]),
    "roles.assign": ("Nadawanie ról użytkownikom", ["user.read", "role.read", "role.manage"]),
}

ROLES = {
    ADMIN_ROLE: list(PERMISSIONS),
    "viewer": ["user.read", "role.read"],
}


class DatabaseManager:
    # USER

    @staticmethod
    def _users(include_inactive: bool = False):
        query = db.session.query(User)
        if not include_inactive:
            query = query.filter(User.status == UserStatus.ACTIVE)
        return query

    def get_users(self, include_inactive: bool = False) -> list[User]:
        return self._users(include_inactive).order_by(User.surname, User.name).all()

    def get_user_by_id(self, user_id: int, include_inactive: bool = False) -> User | None:
        return self._users(include_inactive).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str, include_inactive: bool = False) -> User | None:
        return self._users(include_inactive).filter(User.email == email).first()

    def get_user_by_keycloak_id(
        self, keycloak_id: str, include_inactive: bool = False
    ) -> User | None:
        return self._users(include_inactive).filter(User.keycloak_id == keycloak_id).first()

    def get_users_by_role(self, role_name: str, include_inactive: bool = False) -> list[User]:
        return (
            self._users(include_inactive)
            .join(RoleUser, RoleUser.user_id == User.id)
            .join(Role, Role.id == RoleUser.role_id)
            .filter(Role.role_name == role_name)
            .order_by(User.surname, User.name)
            .all()
        )

    def users_multi_roles(self, include_inactive: bool = False) -> list[User]:
        """Użytkownicy z więcej niż jedną rolą."""
        return (
            self._users(include_inactive)
            .join(RoleUser, RoleUser.user_id == User.id)
            .group_by(User.id)
            .having(func.count(RoleUser.role_id) > 1)
            .order_by(User.surname, User.name)
            .all()
        )

    def create_new_user(
        self,
        keycloak_id: str,
        email: str,
        name: str,
        surname: str,
        identity_provider: str | None = None,
        role_names: list[str] | None = None,
    ) -> User:
        user = User(
            keycloak_id=keycloak_id,
            email=email,
            name=name,
            surname=surname,
            identity_provider=identity_provider,
        )
        db.session.add(user)
        for role_name in role_names or []:
            db.session.add(RoleUser(user=user, role=self._get_role_or_raise(role_name)))
        db.session.commit()
        return user

    def update_user(self, user: User, **fields) -> User:
        allowed = {"email", "name", "surname", "identity_provider", "status"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Cannot update fields: {', '.join(sorted(unknown))}")
        for key, value in fields.items():
            setattr(user, key, value)
        db.session.commit()
        return user

    @staticmethod
    def user_is_active(user: User | None) -> bool:
        return user is not None and user.status == UserStatus.ACTIVE

    def user_is_admin(self, user: User | None) -> bool:
        return self.has_role(user, ADMIN_ROLE)

    def user_can(self, user: User | None, function_code: str) -> bool:
        """Dostęp do funkcji: status -> override -> reguła AND (wszystkie wymagane uprawnienia)."""
        if not self.user_is_active(user):
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

    # ROLE

    @staticmethod
    def get_roles() -> list[Role]:
        return db.session.query(Role).order_by(Role.role_name).all()

    @staticmethod
    def get_role(role_name: str) -> Role | None:
        return db.session.query(Role).filter(Role.role_name == role_name).first()

    def _get_role_or_raise(self, role_name: str) -> Role:
        role = self.get_role(role_name)
        if role is None:
            raise ValueError(f"Role '{role_name}' does not exist")
        return role

    def has_role(self, user: User | None, role_name: str) -> bool:
        if not self.user_is_active(user):
            return False
        return any(role.role_name == role_name for role in user.roles)

    def add_role(self, user: User, role_name: str) -> None:
        role = self._get_role_or_raise(role_name)
        if any(link.role_id == role.id for link in user.role_links):
            return
        db.session.add(RoleUser(user=user, role=role))
        db.session.commit()

    def remove_role(self, user: User, role_name: str) -> None:
        role = self._get_role_or_raise(role_name)
        for link in list(user.role_links):
            if link.role_id == role.id:
                db.session.delete(link)
        db.session.commit()

    # SEED

    @classmethod
    def init_db(cls) -> None:
        """Dane startowe: role z uprawnieniami i funkcjami, potem administratorzy."""
        cls.insert_roles()
        cls.insert_admins()

    @classmethod
    def insert_admins(cls, admins: list[dict] | None = None) -> None:
        """Zakłada administratorów z ADMIN_USERS i nadaje im rolę ADMIN_ROLE.

        Idempotentne: istniejącego użytkownika (po keycloak_id) nie nadpisuje i nie aktywuje,
        tylko dopisuje brakującą rolę. Wymaga wcześniejszego insert_roles().
        """
        if admins is None:
            admins = current_app.config.get("ADMIN_USERS", [])
        manager = cls()
        role = manager._get_role_or_raise(ADMIN_ROLE)
        for admin in admins:
            user = manager.get_user_by_keycloak_id(admin["keycloak_id"], include_inactive=True)
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

    @classmethod
    def insert_roles(cls) -> None:
        """Wgrywa PERMISSIONS, FUNCTIONS i ROLES. Idempotentne: dodaje brakujące, nic nie usuwa."""
        permissions = cls._seed_permissions()
        cls._seed_functions(permissions)
        cls._seed_roles(permissions)
        db.session.commit()

    @staticmethod
    def _seed_permissions() -> dict[str, Permission]:
        permissions = {p.code: p for p in db.session.query(Permission).all()}
        for code, description in PERMISSIONS.items():
            if code not in permissions:
                permissions[code] = Permission(code=code, description=description)
                db.session.add(permissions[code])
        return permissions

    @staticmethod
    def _seed_functions(permissions: dict[str, Permission]) -> None:
        functions = {f.code: f for f in db.session.query(Function).all()}
        for code, (description, required) in FUNCTIONS.items():
            function = functions.get(code)
            if function is None:
                function = Function(code=code, description=description)
                db.session.add(function)
            linked = {link.permission.code for link in function.permission_links}
            for permission_code in set(required) - linked:
                permission = permissions[permission_code]
                db.session.add(PermissionFunction(function=function, permission=permission))

    @staticmethod
    def _seed_roles(permissions: dict[str, Permission]) -> None:
        roles = {r.role_name: r for r in db.session.query(Role).all()}
        for role_name, granted in ROLES.items():
            role = roles.get(role_name)
            if role is None:
                role = Role(role_name=role_name)
                db.session.add(role)
            linked = {link.permission.code for link in role.permission_links}
            for permission_code in set(granted) - linked:
                db.session.add(RolePermission(role=role, permission=permissions[permission_code]))


db_manager = DatabaseManager()
