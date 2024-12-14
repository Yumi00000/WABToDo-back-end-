from django.db import models


class Comment(models.Model):
    member = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, related_name="commentator")
    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, related_name="task_comments")
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    def __str__(self):
        return self.content


class Message(models.Model):
    chat = models.ForeignKey("users.Chat", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, related_name="sender")
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    def __str__(self):
        return self.content


class Notification(models.Model):
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, related_name="notifications")
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content
