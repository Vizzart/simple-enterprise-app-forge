---
name: pm-board
description: Manage SEAF tasks on GitHub — create issues with labels and milestone, add them to the kanban (Project #4), move cards between Todo / In Progress / Test / Done, list and close tasks. Use when the user asks to add a task/ticket, plan work, move or close a card, or show the board ("dodaj zadanie", "przenieś #5 do Test", "co zostało w etapie 0").
---

# pm-board — SEAF kanban on GitHub

Works for any developer: the repo is taken from the current git remote, the board from `project.conf` (next to this file), and "me" is whoever is logged in to `gh`. Never hardcode a username.

The repo is **public** — never put secrets, passwords, internal hostnames or tokens in issues.
Board columns: Todo → In Progress → Test → Done.

## Setup (once per developer)

1. `gh auth login`, then `gh auth refresh -s project` (approve the code in the browser).
2. Have write access to the repo and be added to the project (board → ⋯ → Settings → Manage access) — the project owner does this.
3. Check: `.claude/skills/pm-board/scripts/board.sh` prints the board without errors.

## Ownership

- New issue: assign to the current user (`--assignee @me`) unless the user names someone else (`--assignee <login>`) or says to leave it unassigned.
- Moving to In Progress: `move.sh` assigns the current user if the issue has no assignee.
- "My tasks" → `board.sh --mine`. Never reassign someone else's issue without being asked.

## Labels (required on every issue)

- **Exactly one type:** `bug`, `feature`, `chore`, `docs`, `test`, `learning`
- **At least one area:** `app`, `devops`, `security`
- Optional: `priority:high` (blocks other work), `blocked` (waiting on something external)

Pick labels yourself from the task content; don't create new labels without asking.
Docker, Helm, k8s, ingress, cert-manager, Vault, Harbor, Postgres-in-cluster, CI/CD → `devops`.

## Milestones (stages)

| Milestone | Scope |
|---|---|
| `Etap 0: SEAF k8s-ready` | app ready for containers: stdout logs, /health, prod config |
| `Etap 1: Helm chart` | SEAF chart on local cluster |
| `Etap 2: Ingress + TLS` | ingress-nginx, cert-manager, local CA |
| `Etap 3: PostgreSQL` | in-cluster DB, migrations hook, backups |
| `Etap 4: Vault` | Vault + Vault Secrets Operator |
| `Etap 5: Harbor` | registry, robot accounts, CA trust |
| `Etap 6: Operacje` | backup/restore, upgrades, rebuild drills |

App features unrelated to a stage (forms, login, roles) → no milestone unless the user says otherwise.
Check current milestones with `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`.

## Issue format

- Title: English, imperative, short (`Add /health endpoint`).
- Body:
  ```
  <one or two sentences: what and why>

  **Done when:**
  - [ ] <verifiable outcome>
  ```

## Commands

Run from the repo root. Scripts live next to this file.

```bash
# create issue + put it on the board in Todo
gh issue create --title "..." --body "..." --label feature,app \
  --milestone "Etap 0: SEAF k8s-ready" --assignee @me
.claude/skills/pm-board/scripts/move.sh <issue-number> todo

# move a card: todo | progress | test | done
.claude/skills/pm-board/scripts/move.sh 5 progress

# show board grouped by column (--mine: only my issues)
.claude/skills/pm-board/scripts/board.sh
.claude/skills/pm-board/scripts/board.sh --mine

# lists
gh issue list --milestone "Etap 0: SEAF k8s-ready"
gh issue list --label devops --state all

# close (also moves to Done if the project workflow is enabled; otherwise run move.sh N done)
gh issue close 5 --comment "Done in <commit>"
```

`move.sh` adds the issue to the board if it isn't there yet, so it is safe to call right after `gh issue create`.

## Rules

- Creating several issues at once: show the list (title, labels, milestone) and get a yes first.
- Closing, deleting or transferring issues: only when the user asks.
- Prefer `closes #N` in commit messages over closing manually when the work is committed.
- If a command fails with `missing required scopes [project]`, tell the user to run `! gh auth refresh -s project` and approve the code in the browser — don't work around it.
- If the project can't be found or edited, the developer is probably not added to the project — point them to Setup step 2.
