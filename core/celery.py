import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core", include="core.tasks")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-expired-tokens": {"task": "users.tasks.cleanup_expired_tokens", "schedule": crontab(minute="30")}
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Represents a debugging task that prints details of the current request.

    This function is a Celery task decorated to indicate that it does not
    store the result of its execution. The primary purpose of this task is
    to output the detailed request information to facilitate debugging or
    problem identification.

    Args:
        self: Represents the instance of the task that provides access
            to request-related attributes.
    """
    print(f"Request: {self.request!r}")
