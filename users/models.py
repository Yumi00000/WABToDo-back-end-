from datetime import datetime, timedelta

import jwt
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now

from core import settings


class CustomUser(AbstractUser):
    """
    Admin
    Client
    Executor
    """

    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_team_member = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"user_id: {self.id} | username: {self.username},"


class CustomAuthToken(models.Model):
    """JWT"""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_auth_token")
    key = models.CharField(max_length=512, unique=True)
    user_agent = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_jwt()
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(hours=168)
        return super().save(*args, **kwargs)

    def generate_jwt(self):
        payload = {
            "user_id": self.user.id,
            "username": self.user.username,
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(hours=168),
            "user_agent": self.user_agent,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    def is_valid(self):
        return self.expires_at > now()

    def __str__(self):
        return f"Token owner {self.user.username} - token: {self.key}"


class Team(models.Model):
    leader = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="team_leader")
    status = models.CharField(max_length=11, default="available")

    def __str__(self):
        return f"team_id: {self.id} | status: {self.status}"


class TeamMember(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="team_member")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
