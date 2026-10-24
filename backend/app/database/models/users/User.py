from enum import StrEnum

from app.extensions import db


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class User(db.Model):
    """Osoba w systemie. Uwierzytelnia ją Keycloak; tu tylko dane i status."""

    __tablename__ = "dim_user"

    id = db.Column(db.Integer, primary_key=True)
    # claim `sub` z tokenu Keycloak — stały identyfikator, nie łączymy kont po e-mailu
    keycloak_id = db.Column(db.String(255), unique=True, nullable=False)
    # `keycloak` / `entra` / `google` — z claimu `identity_provider`, tylko informacyjnie
    identity_provider = db.Column(db.String(50))
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    status = db.Column(
        db.Enum(
            UserStatus,
            name="user_status",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )

    role_links = db.relationship(
        "RoleUser", back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    function_overrides = db.relationship(
        "UserFunctionOverride",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    roles = db.relationship("Role", secondary="map_role_user", viewonly=True)

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email}>"
