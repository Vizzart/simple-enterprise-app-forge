from app.extensions import db


class RoleUser(db.Model):
    """Przypisanie roli do użytkownika."""

    __tablename__ = "map_role_user"
    __table_args__ = (db.UniqueConstraint("user_id", "role_id"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("dim_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id = db.Column(
        db.Integer, db.ForeignKey("dim_role.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user = db.relationship("User", back_populates="role_links")
    role = db.relationship("Role", back_populates="user_links")
