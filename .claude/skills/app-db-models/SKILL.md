---
name: app-db-models
description: Conventions for SQLAlchemy models, table naming and Alembic migrations in SEAF. Use when adding or changing a model, table, column, relation or migration, or when writing raw SQL against the app DB.
---

# DB models and naming

Schema, relations and access rules: the `app-rbac` skill (diagram: `.claude/skills/app-rbac/schema.drawio`). Keep it in sync with the models.

## Naming
- Tables and columns: `snake_case`, singular nouns (`dim_user`, not `dimUser` / `dim_users`).
- `dim_` prefix: entities / dictionaries (`dim_user`, `dim_role`, `dim_permission`, `dim_function`).
- `map_` prefix: join tables, named after both sides (`map_role_user`, `map_role_permission`).
- Primary key: `id`. Foreign key: `<table without prefix>_id` (`user_id`, `role_id`).
- Model classes: PascalCase without the prefix (`User` → `dim_user`, `RoleUser` → `map_role_user`), with explicit `__tablename__`.

## Structure
- Models live in `backend/app/database/models/<group>/<ClassName>.py`, one class per file: `users/`, `roles/`, `permissions/`, `functions/`, `associations/` (all `map_` tables).
- Each group `__init__.py` re-exports its classes; `models/__init__.py` imports every group so Alembic autogenerate sees all tables. Import models as `from app.database.models import User`.
- Cross-group relationships use class names as strings (`db.relationship("Role", ...)`); model modules never import each other.
- `map_` tables are association objects (own `id`); `dim_` models expose them as `*_links` with `cascade="all, delete-orphan", passive_deletes=True`, plus read-only shortcuts via `secondary=..., viewonly=True` (e.g. `User.roles`). Write through the association objects.
- Use the classic `db.Column(db.Integer, ...)` / `db.relationship(...)` style — **not** `Mapped[...]` / `mapped_column` (user preference: easier to read). Everything through `db.` (`db.String`, `db.ForeignKey`, `db.UniqueConstraint`).
- `db.Column` is NULL-able by default: every required column gets explicit `nullable=False`.
- Foreign keys are `nullable=False` in `map_` tables, with `ondelete="CASCADE"`.
- Every `map_` table has a `UniqueConstraint` on its FK pair.
- Business identifiers (`code`, `role_name`, `keycloak_id`) are `unique=True`.
- Enumerated columns: Python `StrEnum` + `db.Enum(..., native_enum=False, create_constraint=True, values_callable=...)` (varchar + CHECK, no Postgres enum type).

## Auth constraints
- Login is Keycloak-only: never add password, password-hash or local login columns.
- Users are identified by `dim_user.keycloak_id` (token `sub`), never matched by email.
- Roles and permissions live in the app DB, not in Keycloak.
- Function access (AND rule): a user may run a function only if their role permissions include **all** permissions mapped to it in `map_permission_function`. A function with no mapped permissions is denied. A `map_user_function_override` row wins over this (`allow` true/false). Never implement it as "any permission".

## Usage
- Write through association objects: `db.session.add(RoleUser(user=u, role=r))`; read via `viewonly` shortcuts (`user.roles`, `role.permissions`, `function.required_permissions`) — appending to them saves nothing.
- `db.ForeignKey(...)` takes the **table** name (`"dim_user.id"`), `db.relationship(...)` takes the **class** name (`"User"`).

## Migrations
- After changing models: `docker compose exec backend flask db migrate -m "<what changed>"`, review the generated file in `backend/migrations/versions/` (autogenerate misses renames), then `flask db upgrade`.
- Never edit a migration that is already on `main`; add a new one.
- When the schema changes, update the `app-rbac` skill table and `.claude/skills/app-rbac/schema.drawio` in the same commit.
