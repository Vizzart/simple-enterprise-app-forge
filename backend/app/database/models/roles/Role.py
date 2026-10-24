from app.extensions import db


class Role(db.Model):
    """Rola w systemie. Każda rola powinna mieć co najmniej jedno uprawnienie."""

    __tablename__ = "dim_role"

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(100), unique=True, nullable=False)

    user_links = db.relationship(
        "RoleUser", back_populates="role", cascade="all, delete-orphan", passive_deletes=True
    )
    permission_links = db.relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan", passive_deletes=True
    )
    users = db.relationship("User", secondary="map_role_user", viewonly=True)
    permissions = db.relationship("Permission", secondary="map_role_permission", viewonly=True)

    def __repr__(self) -> str:
        return f"<Role {self.role_name}>"
