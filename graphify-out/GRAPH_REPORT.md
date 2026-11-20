# Graph Report - simple-enterprise-app-forge  (2026-10-28)

## Corpus Check
- Corpus is ~8,227 words - fits in a single context window. You may not need a graph.

## Summary
- 364 nodes · 535 edges · 20 communities (15 shown, 5 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- User & Role Models
- Auth Decorators
- Infra Compose (Keycloak/Registry)
- App Compose Stack
- Project Overview (CLAUDE.md)
- RBAC Association Models
- RBAC Seed YAML
- Config & Celery Init
- Permission & Seed Loader
- Dependencies & DB Conventions
- Keycloak/GitLab Services
- Compose Service Options
- Compose Volumes
- Celery Task Rules
- PM Board Skill
- board.sh
- move.sh
- SEAF Root

## God Nodes (most connected - your core abstractions)
1. `User` - 23 edges
2. `gitlab` - 11 edges
3. `login_required()` - 10 edges
4. `keycloak` - 10 edges
5. `sync_user()` - 9 edges
6. `verify_token()` - 9 edges
7. `Role` - 9 edges
8. `backend` - 9 edges
9. `insert_roles()` - 8 edges
10. `insert_admins()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Keycloak-only authentication (JWKS token verification)` --references--> `PyJWT`  [INFERRED]
  .claude/skills/app-rbac/SKILL.md → backend/app/requirements.txt
- `Keycloak-only authentication (JWKS token verification)` --conceptually_related_to--> `Keycloak 26 (OIDC)`  [INFERRED]
  .claude/skills/app-rbac/SKILL.md → CLAUDE.md
- `psycopg 3` --implements--> `PostgreSQL 18 app DB`  [INFERRED]
  backend/app/requirements.txt → CLAUDE.md
- `current_user()` --uses--> `User`  [INFERRED]
  backend/app/auth/decorators.py → backend/app/database/models/users/User.py
- `_seed_functions()` --calls--> `PermissionFunction`  [INFERRED]
  backend/app/database/seed/loader.py → backend/app/database/models/associations/PermissionFunction.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Function access control flow** — claude_skills_app_rbac_skill_keycloak_auth, claude_skills_app_rbac_skill_jit_provisioning, claude_skills_app_rbac_skill_function_access, claude_skills_app_rbac_skill_override [EXTRACTED 0.95]
- **Endpoint protection via decorators and RBAC seed** — claude_md_restx_api, claude_md_auth_module, claude_md_seed_rbac_yaml, claude_md_rbac_access [INFERRED 0.85]
- **Local dev stack driven by Makefile** — claude_md_makefile, claude_md_docker_compose, claude_md_infra_dev, claude_md_envs [INFERRED 0.85]
- **Background job pipeline** — claude_skills_app_celery_tasks_skill_flasktask, claude_skills_app_celery_tasks_skill_beat, backend_app_requirements_txt_celery [INFERRED 0.85]

## Communities (20 total, 5 thin omitted)

### Community 0 - "User & Role Models"
Cohesion: 0.08
Nodes (23): sync_user(), Role, User, add_role(), get_or_raise(), get_role(), get_roles(), has_role() (+15 more)

### Community 1 - "Auth Decorators"
Cohesion: 0.08
Nodes (11): current_user(), function_required(), decorator(), wrapper(), login_required(), wrapper(), InvalidToken, _jwks_client() (+3 more)

### Community 2 - "Infra Compose (Keycloak/Registry)"
Cohesion: 0.06
Nodes (39): keycloak-db, KC_DB, KC_DB_URL, KC_HEALTH_ENABLED, KC_HOSTNAME, KC_HOSTNAME_BACKCHANNEL_DYNAMIC, REGISTRY_STORAGE_DELETE_ENABLED, interval (+31 more)

### Community 3 - "App Compose Stack"
Cohesion: 0.06
Nodes (34): build, command, depends_on, env_file, image, networks, ports, volumes (+26 more)

### Community 4 - "Project Overview (CLAUDE.md)"
Cohesion: 0.08
Nodes (34): psycopg 3, app/auth token verification and decorators, Celery + Redis background jobs, Config class (env vars only), Coding conventions, SQLAlchemy models and repositories, Dev tools: ruff, mypy, pytest, docker-compose app stack (+26 more)

### Community 5 - "RBAC Association Models"
Cohesion: 0.11
Nodes (6): PermissionFunction, RolePermission, RoleUser, UserFunctionOverride, Function, UserStatus

### Community 6 - "RBAC Seed YAML"
Cohesion: 0.08
Nodes (23): permissions, functions, roles.assign, roles.list, users.edit, users.list, permissions, role.manage (+15 more)

### Community 7 - "Config & Celery Init"
Cohesion: 0.13
Nodes (4): celery_init_app(), Config, create_app(), make_shell_context()

### Community 8 - "Permission & Seed Loader"
Cohesion: 0.17
Nodes (8): Permission, init_db(), insert_admins(), insert_roles(), load_rbac_seed(), _seed_functions(), _seed_permissions(), _seed_roles()

### Community 9 - "Dependencies & DB Conventions"
Cohesion: 0.11
Nodes (19): Dev tools (ruff, mypy, pytest), celery[redis], Flask / Flask-RESTX, PyJWT, Runtime requirements, SQLAlchemy / Flask-SQLAlchemy / Alembic, Association objects with viewonly shortcuts, Alembic migrations (+11 more)

### Community 10 - "Keycloak/GitLab Services"
Cohesion: 0.14
Nodes (14): keycloak, GITLAB_OMNIBUS_CONFIG, depends_on, env_file, environment, hostname, image, networks (+6 more)

### Community 11 - "Compose Service Options"
Cohesion: 0.17
Nodes (12): env_file, healthcheck, image, networks, ports, restart, volumes, interval (+4 more)

### Community 12 - "Compose Volumes"
Cohesion: 0.18
Nodes (11): name, name, name, name, name, volumes, gitlab-config, gitlab-data (+3 more)

### Community 13 - "Celery Task Rules"
Cohesion: 0.50
Nodes (3): Celery beat (single instance), Celery tasks skill, celery_init_app / FlaskTask

### Community 14 - "PM Board Skill"
Cohesion: 0.50
Nodes (4): pm-board skill, GitHub Project kanban columns, Issue labels scheme, Milestones Etap 0-6 (k8s roadmap)

## Knowledge Gaps
- **24 isolated node(s):** `seaf`, `celery_init_app / FlaskTask`, `Celery beat (single instance)`, `Association objects with viewonly shortcuts`, `Alembic migrations` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 176 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `services` connect `Infra Compose (Keycloak/Registry)` to `Keycloak/GitLab Services`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `User` (e.g. with `current_user()` and `sync_user()`) actually correct?**
  _`User` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `seaf`, `celery_init_app / FlaskTask`, `Celery beat (single instance)` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `User & Role Models` be split into smaller, more focused modules?**
  _Cohesion score 0.08484848484848485 - nodes in this community are weakly interconnected._
- **Why does `User` connect `User & Role Models` to `Permission & Seed Loader`, `Auth Decorators`, `RBAC Association Models`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `login_required()` (e.g. with `wrapper()` and `InvalidToken`) actually correct?**
  _`login_required()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Auth Decorators` be split into smaller, more focused modules?**
  _Cohesion score 0.08048780487804878 - nodes in this community are weakly interconnected._