from core import settings
from django.db import models

from tasks.models import Task
from users.models import Team


class Order(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_orders")
    name = models.CharField(max_length=128)
    description = models.TextField()
    accepted = models.BooleanField(default=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_orders", null=True, blank=True)
    tasks = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_orders", null=True, blank=True)
    deadline = models.DateField()
    createdAt = models.DateTimeField(auto_now_add=True, blank=True)
    updatedAt = models.DateTimeField(null=True, blank=True)
    acceptedAt = models.DateTimeField(null=True, blank=True)
