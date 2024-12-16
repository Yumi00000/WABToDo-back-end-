from rest_framework import serializers

from websocket.models import Comment, Notification, Message


class CommentSerializer(serializers.ModelSerializer):
    content = serializers.JSONField()
    member_id = serializers.IntegerField(write_only=True)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comment
        fields = ["content", "member_id", "task_id", "created_at"]
        read_only_fields = ["created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Notification
        fields = ["user_id", "content", "created_at"]
        read_only_fields = ["created_at"]


class MessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.IntegerField(write_only=True)
    sender_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Message
        fields = ["chat_id", "sender_id", "content", "created_at"]
        read_only_fields = ["created_at"]
