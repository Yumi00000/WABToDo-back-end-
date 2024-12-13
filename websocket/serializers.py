from rest_framework import serializers
from websocket.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)

    class Meta:
        model = Comment
        fields = ["username", "content", "member_id", "task_id", "created_at"]
        read_only_fields = ["created_at"]
