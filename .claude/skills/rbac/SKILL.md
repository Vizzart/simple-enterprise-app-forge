---
name: rbac
description: SEAF authentication (Keycloak-only OIDC) and RBAC model - tables, relations, business rules and the function-access algorithm. Use when working on login, users, roles, permissions, functions, overrides, access checks, or when asked how authorization works.
---

# Auth + RBAC

Diagram: `schema.drawio` in this folder (open in draw.io / app.diagrams.net). Models: `backend/app/database/models/`. Model-writing conventions: the `db-models` skill.

## Authentication: Keycloak only
- The app has **no local login and stores no passwords**. Keycloak (OIDC) authenticates; the app only verifies Keycloak tokens (JWKS) and authorizes with the tables below.
- A user is identified by the token `sub` claim, stored in `dim_user.keycloak_id`. Never match or merge accounts by email (it can change).
- Flow: the SPA (client `seaf-frontend`, public, Authorization Code + PKCE S256) logs in at Keycloak and calls the API with `Authorization: Bearer <access token>`. The backend never redirects to Keycloak; it verifies the token signature via JWKS (`KEYCLOAK_JWKS_URL`), `iss` == `KEYCLOAK_ISSUER` and `aud` contains `KEYCLOAK_AUDIENCE` (`seaf-api`, added by an audience mapper). Flask-JWT-Extended is not used for Keycloak tokens.
- Local dev realm: `infra/dev/keycloak/import/seaf-realm.json` (test users `anna`, `piotr`, `ewa`, `jan` / `test`; password grant enabled on `seaf-frontend` for curl/Swagger testing — dev only).
- First login creates the `dim_user` row (just-in-time provisioning). Every login refreshes `email`, `name`, `surname` from claims `email`, `given_name`, `family_name`.
- Roles and permissions are managed in the app DB, **not** in Keycloak roles.
- External logins (Microsoft Entra ID, Google) are configured only in Keycloak as **Identity Providers** (identity brokering). The app keeps talking only to Keycloak: no app code or schema change. `dim_user.identity_provider` (optional, from an `identity_provider` claim mapper) is informational only.

## Tables
`dim_` = entities, `map_` = join tables (association objects with own `id`). All `map_` FKs are NOT NULL, `ON DELETE CASCADE`, indexed, and each `map_` table is UNIQUE on its FK pair.

| Table (model) | Columns | Purpose / rules |
|---|---|---|
| `dim_user` (`User`) | `id`, `keycloak_id` UQ, `identity_provider` null, `email`, `name`, `surname`, `status` (`active`/`inactive`, CHECK, default `active`) | A person. `status = inactive` blocks the user in the app even if Keycloak lets them in. A user can have many roles. |
| `dim_role` (`Role`) | `id`, `role_name` UQ | A role. Can be assigned to many users. Should have at least one permission. |
| `dim_permission` (`Permission`) | `id`, `code` UQ, `description` null | Permission (access level). `code` is used in code, e.g. `invoice.read`. |
| `dim_function` (`Function`) | `id`, `code` UQ, `description` null | System function (action, module). Should require at least one permission. |
| `map_role_user` (`RoleUser`) | `user_id` → `dim_user`, `role_id` → `dim_role` | Role assignment. |
| `map_role_permission` (`RolePermission`) | `role_id` → `dim_role`, `permission_id` → `dim_permission` | Permissions granted by a role. |
| `map_permission_function` (`PermissionFunction`) | `function_id` → `dim_function`, `permission_id` → `dim_permission` | Permissions **required** by a function. |
| `map_user_function_override` (`UserFunctionOverride`) | `user_id` → `dim_user`, `function_id` → `dim_function`, `allow` bool | Optional per-user override; only applies when a row exists. |

## Function access algorithm
1. Valid Keycloak token → load user by `keycloak_id` (create on first login).
2. `status != active` → deny.
3. Row in `map_user_function_override` for (user, function) → `allow` decides (true grants, false denies), regardless of roles.
4. Otherwise apply the **AND rule**: allow only if the user's permissions (`map_role_user` → `map_role_permission`) contain **all** permissions in `map_permission_function` for that function. A function with no required permissions is **denied**.

Never implement step 4 as "any permission". Example: function `invoice.approve` requires `invoice.read` + `invoice.approve`; a user with only `invoice.read` is denied.
- Adding a permission to a function **narrows** access.
- When several roles should reach one function, give them a shared permission (e.g. `report.sales.view`) instead of mapping alternative permissions to the function.

## Granting and changing access
Bundles of permissions are **roles** (job positions), never functions; functions only declare requirements. Users get roles; a user may hold several roles and their permissions are summed. Per-user exceptions are overrides. There are **no add-on roles / extra per-user scope** — do not propose them.

| Need | Do |
|---|---|
| New job position | new role with permissions |
| Scope of a whole position changes | change the role's permissions (affects everyone with it) |
| One user must use one function their roles don't allow | override, `allow = true` |
| One user must NOT use a function their roles allow | override, `allow = false` |
| Exception ends | delete the override row |

Override semantics:
- One row = one user + one function + decision. It grants **no permission**, so no other function opens.
- Wins over roles both ways, but never over `status` (inactive users are denied first).
- Never expires on its own (no validity dates) and survives role changes; it stays until the row is deleted.
- If the same function is overridden for several users with the same role, the role should get the permission instead.

There is **no** direct user→permission or role→function assignment; do not add such tables.

## Keeping it in sync
When the schema changes, update in the same commit: the models, a new Alembic migration, this skill's table, and `schema.drawio`.
