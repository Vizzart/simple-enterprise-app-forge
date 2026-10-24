from app.extensions import db


class Permission(db.Model):
    """Uprawnienie (poziom dostępu). `code` jest używany w kodzie aplikacji."""

    __tablename__ = "dim_permission"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    role_links = db.relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    function_links = db.relationship(
        "PermissionFunction",
        back_populates="permission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"
