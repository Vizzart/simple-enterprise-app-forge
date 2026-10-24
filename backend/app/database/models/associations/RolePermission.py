from app.extensions import db


class RolePermission(db.Model):
    """Przypisanie uprawnienia do roli."""

    __tablename__ = "map_role_permission"
    __table_args__ = (db.UniqueConstraint("role_id", "permission_id"),)

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(
        db.Integer, db.ForeignKey("dim_role.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id = db.Column(
        db.Integer,
        db.ForeignKey("dim_permission.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = db.relationship("Role", back_populates="permission_links")
    permission = db.relationship("Permission", back_populates="role_links")
