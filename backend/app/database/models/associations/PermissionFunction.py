from app.extensions import db


class PermissionFunction(db.Model):
    """Uprawnienie wymagane przez funkcję (funkcja wymaga wszystkich — reguła AND)."""

    __tablename__ = "map_permission_function"
    __table_args__ = (db.UniqueConstraint("function_id", "permission_id"),)

    id = db.Column(db.Integer, primary_key=True)
    function_id = db.Column(
        db.Integer, db.ForeignKey("dim_function.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id = db.Column(
        db.Integer,
        db.ForeignKey("dim_permission.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    function = db.relationship("Function", back_populates="permission_links")
    permission = db.relationship("Permission", back_populates="function_links")
