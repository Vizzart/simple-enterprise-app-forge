from app.extensions import db


class UserFunctionOverride(db.Model):
    """Nadpisanie dostępu do funkcji dla użytkownika; ma pierwszeństwo przed rolami."""

    __tablename__ = "map_user_function_override"
    __table_args__ = (db.UniqueConstraint("user_id", "function_id"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("dim_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    function_id = db.Column(
        db.Integer, db.ForeignKey("dim_function.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # True — nadaje dostęp, False — odbiera, niezależnie od ról
    allow = db.Column(db.Boolean, nullable=False)

    user = db.relationship("User", back_populates="function_overrides")
    function = db.relationship("Function", back_populates="user_overrides")
