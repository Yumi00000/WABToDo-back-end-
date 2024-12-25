from rest_framework import serializers

from websocket.models import Comment, Notification, Message


class CommentSerializer(serializers.ModelSerializer):
    content = serializers.JSONField()
    member_id = serializers.IntegerField(required=False)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comment
        fields = ["content", "member_id", "task_id", "created_at"]
        read_only_fields = ["created_at"]


class UpdateCommentSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(write_only=True)
    member_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Comment
        fields = ["content", "updated_at", "pk", "member_id", "task_id"]
        read_only_fields = ["task_id", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Notification
        fields = ["user_id", "content", "created_at"]
        read_only_fields = ["created_at"]


class MessageSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(read_only=True)
    chat_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()
    sender_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Message
        fields = ["chat_id", "content", "created_at", "sender_id", "pk"]
        read_only_fields = ["created_at"]


class UpdateMessageSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(write_only=True)
    chat_id = serializers.IntegerField(write_only=True)
    sender_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Message
        fields = ["pk", "chat_id", "sender_id", "content", "updated_at"]
        read_only_fields = ["updated_at"]


def get_serializer(serializer_label):
    serializers = {
        "CommentSerializer": CommentSerializer,
        "NotificationSerializer": NotificationSerializer,
        "MessageSerializer": MessageSerializer,
        "UpdateMessageSerializer": UpdateMessageSerializer,
        "UpdateCommentSerializer": UpdateCommentSerializer,
    }
    serializer = serializers[serializer_label]
    return serializer
