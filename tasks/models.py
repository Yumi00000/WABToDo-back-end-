from django.db import models

from core import settings
from users.models import Team


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="tasks_as_executor"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tasks")
    status = models.CharField(max_length=11, default="pending")
    deadline = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Task title: {self.title}"
