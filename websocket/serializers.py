from rest_framework import serializers

from websocket.models import Comment, Notification, Message


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.

    The CommentSerializer is responsible for transforming Comment model instances
    into JSON representation and vice versa. This serializer also dictates which
    fields are included and specifies their configuration, such as read-only
    fields, write-only fields, and required fields.

    Attributes:
        content: A JSON field representing the main content of the comment.
        member_id: An optional integer field representing the ID of the associated
            member. It is not required.
        task_id: An integer field, write-only, representing the ID of the associated
            task.

    Meta:
        model: Specifies the Comment model to be serialized.
        fields: Defines the fields to be included in the serialized representation:
            content, member_id, task_id, and created_at.
        read_only_fields: Specifies 'created_at' as a read-only field, meaning
            it cannot be modified through the serializer.
    """
    content = serializers.JSONField()
    member_id = serializers.IntegerField(required=False)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comment
        fields = ["content", "member_id", "task_id", "created_at"]
        read_only_fields = ["created_at"]


class UpdateCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a comment.

    This serializer is designed to handle the process of updating comments
    using specific fields. It ensures that only the allowed fields are updated
    and provides validation for the input data. This serializer is linked to the
    Comment model and includes only the necessary fields for the update process.
    It enforces write-only access for input fields and read-only access for
    specific fields as required.

    Attributes:
        pk: IntegerField used as a write-only field to identify the primary key
            of the comment to be updated.
        member_id: IntegerField used as a write-only field to specify the ID of
            the member initiating the update.
        content: JSONField used to hold the updated comment content.

    Meta:
        model: The model associated with this serializer, which is Comment.
        fields: List of all fields included in the serializer - "content",
            "updated_at", "pk", "member_id", "task_id".
        read_only_fields: Fields marked as read-only - "task_id", "updated_at".
    """
    pk = serializers.IntegerField(write_only=True)
    member_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Comment
        fields = ["content", "updated_at", "pk", "member_id", "task_id"]
        read_only_fields = ["task_id", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer class for handling Notification model data.

    This class is used to serialize and deserialize data related to the Notification model.
    It provides functionalities to manage the fields and their validation while interacting
    with Notification objects, ensuring accurate data serialization for various operations.

    Attributes:
        user_id (int): Represents the ID of the user associated with the notification
            (write-only field during serialization).
        content (dict): A JSON field containing the content data of the notification.

    Meta-class attributes:
        model: Indicates this serializer works with the Notification model.
        fields (list): Specifies the fields included in the serialized output.
        read_only_fields (list): Defines fields that are read-only in serialized output.
    """
    user_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Notification
        fields = ["user_id", "content", "created_at"]
        read_only_fields = ["created_at"]


class MessageSerializer(serializers.ModelSerializer):
    """
    A serializer class for representing and validating Message model data.

    This class defines the structure and specification for serializing and
    deserializing `Message` model instances, handling requirements such as
    read-only and write-only fields as well as data validation.

    Attributes:
        pk (serializers.IntegerField): Represents the primary key of the Message
            object. This field is marked as read-only.
        chat_id (serializers.IntegerField): Represents the identifier of the chat
            associated with the Message. This field is write-only.
        content (serializers.JSONField): Represents the message content in JSON
            format. This field is neither read-only nor write-only.
        sender_id (serializers.IntegerField): Represents the identifier of the
            sender of the Message. This field is read-only.

    Nested Meta:
        Provides metadata for the serializer.
    """
    pk = serializers.IntegerField(read_only=True)
    chat_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()
    sender_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Message
        fields = ["chat_id", "content", "created_at", "sender_id", "pk"]
        read_only_fields = ["created_at"]


class UpdateMessageSerializer(serializers.ModelSerializer):
    """
    Serializer class for updating a message.

    This class is used to serialize and deserialize data for updating a message
    instance based on the provided fields. It ensures that specified fields
    are properly validated and transformed before being used to update the
    corresponding message record in the database.

    Attributes:
        pk: Primary key of the message to be updated.
        chat_id: Identifier of the chat to which the message belongs.
        sender_id: Identifier of the user who sent the message.
        content: The content of the message, expected to be a JSON object.

    """
    pk = serializers.IntegerField(write_only=True)
    chat_id = serializers.IntegerField(write_only=True)
    sender_id = serializers.IntegerField(write_only=True)
    content = serializers.JSONField()

    class Meta:
        model = Message
        fields = ["pk", "chat_id", "sender_id", "content", "updated_at"]
        read_only_fields = ["updated_at"]


def get_serializer(serializer_label):
    """
        Returns a serializer class based on the provided serializer label.

        This function maps a string label to its respective serializer class,
        allowing dynamic selection of serializers at runtime. Serializer
        classes must be pre-defined and included in the mapping dictionary.

        Parameters:
        serializer_label (str): The label identifying the desired serializer.

        Returns:
        Type[BaseSerializer]: The serializer class corresponding to the given
        label.

        Raises:
        KeyError: If the serializer label is not found in the mapping dictionary.
    """
    serializers = {
        "CommentSerializer": CommentSerializer,
        "NotificationSerializer": NotificationSerializer,
        "MessageSerializer": MessageSerializer,
        "UpdateMessageSerializer": UpdateMessageSerializer,
        "UpdateCommentSerializer": UpdateCommentSerializer,
    }
    serializer = serializers[serializer_label]
    return serializer
