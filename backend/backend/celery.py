import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# DLQ setup using Redis:
# Celery doesn't natively do RabbitMQ-style DLQ on Redis, but we can configure task routing
# and a custom base task class to push failed messages to a DLQ queue.
app.conf.task_routes = {"dlq_tasks.*": {"queue": "dlq"}}

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
