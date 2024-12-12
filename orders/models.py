from core import settings
from django.db import models

from users.models import Team


class Order(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_orders")
    name = models.CharField(max_length=128)
    description = models.TextField()
    accepted = models.BooleanField(default=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_orders", blank=True)
    tasks = models.ManyToManyField("tasks.Task", related_name="orders", blank=True)
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="active")

    def __str__(self):
        return f"Order name: {self.name}"
