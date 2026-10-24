from celery import Celery, Task
from celery.schedules import crontab
from flask import Flask, app

from app.config import Config


def celery_init_app(app: Flask)-> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    #TODO task
    celery_app.conf.update(app.config["CELERY"])
    app.extensions["celery"] = celery_app
    return celery_app




