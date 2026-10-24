         ---
name: app-celery-tasks
description: How background and periodic jobs work in SEAF (Celery + Redis) and how to write them. Use when adding or changing a Celery task, a beat schedule, the worker service, or app/celery_init.py, or when asked how background jobs work.
---

# Celery tasks

## Architecture
`backend` (Flask) → `task.delay()` → `redis` (broker, compose service) → `worker` (Celery, compose service `celery -A run worker -B`).
- The worker runs the **same code and image** as the backend, with the same `.envs/.flask`.
- `-B` runs beat (scheduler) inside the worker: fine locally. In k8s run beat as **exactly one** separate pod (`celery -A run beat`) and workers without `-B`, otherwise each worker fires every periodic job.
- Config: `Config.CELERY` in `app/config.py` (`broker_url` / `result_backend` = `redis://redis`, `task_ignore_result = True`, `worker_cancel_long_running_tasks_on_connection_loss = True`). Inside compose, use service names (`redis`), not `localhost`.
****
## Integration (`app/celery_init.py`)
`celery_init_app(app)` creates the Celery app with a `FlaskTask` base class whose `__call__` wraps `run()` in `app.app_context()`, so tasks can use `db.session` and `current_app`. It is stored in `app.extensions["celery"]`; `run.py` exposes it as `celery_app`, which `celery -A run` discovers.

## Writing a task
- Put tasks in `backend/app/tasks/<area>.py` and decorate with `@shared_task` (never import the Celery app object into task modules).
- Arguments and return values must be JSON-serializable: pass ids (`user.id`), never ORM objects; reload the object inside the task.
- Results are ignored by default; set `@shared_task(ignore_result=False)` only when the caller reads the result.
- Make tasks idempotent: they may run twice after a broker reconnect or retry.
- Call with `task.delay(...)` or `task.apply_async(args=[...], countdown=60)`; never call a slow task synchronously from a request.

```python
from celery import shared_task

from app.database.models import User
from app.extensions import db


@shared_task
def deactivate_user(user_id: int) -> None:
    user = db.session.get(User, user_id)
    ...
    db.session.commit()
```

## Periodic jobs
Add to `Config.CELERY["beat_schedule"]`:
```python
"beat_schedule": {
    "nightly-cleanup": {"task": "app.tasks.cleanup.run", "schedule": crontab(hour=2, minute=0)},
},
```
Use Celery beat for scheduling, not APScheduler (it runs inside every Flask replica).

## Commands
- Logs: `docker compose logs -f worker`
- Registered / running tasks: `docker compose exec worker celery -A run inspect registered` / `inspect active`
- The worker does not auto-reload: `docker compose restart worker` after changing task code.
