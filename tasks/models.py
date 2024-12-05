from django.db import models

from core import settings


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="tasks_as_executor"
    )
    team = models.ForeignKey("users.Team", on_delete=models.CASCADE, related_name="tasks_team")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="tasks_order", null=True)
    status = models.CharField(max_length=11, default="pending")
    deadline = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Task title: {self.title}"
