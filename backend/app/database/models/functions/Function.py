from app.extensions import db


class Function(db.Model):
    """Funkcja systemu (akcja, moduł). Wymaga WSZYSTKICH przypisanych uprawnień (reguła AND)."""

    __tablename__ = "dim_function"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    permission_links = db.relationship(
        "PermissionFunction",
        back_populates="function",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user_overrides = db.relationship(
        "UserFunctionOverride",
        back_populates="function",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    required_permissions = db.relationship(
        "Permission", secondary="map_permission_function", viewonly=True
    )

    def __repr__(self) -> str:
        return f"<Function {self.code}>"
