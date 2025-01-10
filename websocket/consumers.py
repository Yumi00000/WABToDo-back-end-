import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from core.tasks import send_email
from users.models import CustomUser, Participant, CustomAuthToken, Chat
from websocket.models import Comment, Notification, Message
from websocket.serializers import (
    CommentSerializer,
    NotificationSerializer,
    MessageSerializer,
    UpdateCommentSerializer,
    UpdateMessageSerializer,
)

logger = logging.getLogger(__name__)


@sync_to_async
def get_username(user_pk):
    """
    A function to asynchronously retrieve the username of a user based on their
    primary key.

    This function is designed to fetch the username of a specific user by their
    primary key from the database and make the operation compatible with async
    code through the sync_to_async decorator.

    Arguments:
        user_pk (int): The primary key of the user whose username will be
                       retrieved.

    Returns:
        str: The username of the user.
    """
    return CustomUser.objects.get(id=user_pk).username


@sync_to_async
def get_recipients_emails(recipients_pk):
    """
    Retrieve the email addresses of recipients based on their primary keys.

    This function fetches the email addresses of users by retrieving them from the
    database using their primary keys.

    Parameters:
        recipients_pk (list[int]): A list of primary keys identifying the recipients.

    Returns:
        list[str]: A list of email addresses corresponding to the provided primary keys.
    """
    return [CustomUser.objects.get(id=recipient_pk).email for recipient_pk in recipients_pk]


class BaseAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    """
    BaseAsyncWebsocketConsumer class is designed to handle WebSocket connections and
    manage communication between a Django application and clients asynchronously.

    This class serves as a foundation for creating WebSocket consumers that require
    group-based communication, data streaming, and sending existing data in chunks
    to connected clients. It provides methods to handle connection establishment,
    disconnection, and synchronous interaction with external tasks or services.

    Attributes:
        headers (dict): Stores headers retrieved from the WebSocket scope.
        group_name (str or None): Unique identifier for the WebSocket group.
        instance (Any or None): Represents a model instance associated with the
            consumer.
        instance_serializer (Any or None): Serializer class linked to the instance.
        type (Any or None): Type indicator for custom usage.
        pk (Any or None): Primary key extracted from the URL route.
        filter (str): Field name used for filtering data.
        batch_size (int): Number of data records to fetch or send per batch.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {}
        self.group_name = None
        self.instance = None
        self.instance_serializer = None
        self.type = None
        self.pk = None
        self.filter = ""
        self.batch_size = 50

    async def connect(self):
        self.headers = self.scope.get("headers", [])
        self.pk = self.scope["url_route"]["kwargs"]["pk"]
        self.group_name = f"{self.group_name}_{self.pk}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_existing_content(self.pk)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.close()
        logger.info("WebSocket disconnected")

    async def send_existing_content(self, pk, last_item_id=None):
        from core.tasks import send_chunked_data

        filter_kwargs = {f"{self.filter}": pk}
        if last_item_id:
            filter_kwargs["id__lt"] = last_item_id  # Fetch items with IDs greater than the last sent

        send_chunked_data.delay(
            group_name=self.group_name,
            instance_model=self.instance.__name__,  # Send model name as string
            instance_serializer_class=self.instance_serializer.__name__,  # Send serializer name as string
            filter_kwargs=filter_kwargs,
            batch_size=self.batch_size,
        )

    async def send_data_chunk(self, event):
        await self.send(text_data=event["message"])


class CommentConsumer(BaseAsyncWebsocketConsumer):
    """
    Handles WebSocket communication for managing comments, including creating, updating,
    deleting, and retrieving comment data in real time.

    This class extends BaseAsyncWebsocketConsumer and manages real-time communication
    via WebSocket for a group called "comments". It processes incoming actions to handle
    CRUD operations on comments, validates input data, and sends serialized responses
    back to the WebSocket group. It can also handle batch data retrieval for pagination.
    Serialization and validation are performed using Django REST Framework serializers,
    and permission checks are implemented where necessary.

    Attributes:
        group_name: The name of the WebSocket group ("comments").
        instance: The model associated with the consumer (Comment).
        type: The type of action broadcasted ("send_comment").
        instance_serializer: The serializer used for serializing Comment objects.
        filter: The filtering field identifier used for batch data retrieval ("task_id").

    Methods:
        __init__(*args, **kwargs)
            Initializes the WebSocket consumer, setting up default attributes.

        disconnect(close_code: int)
            Disconnects the WebSocket and removes it from the group.

        receive(text_data: str, bytes_data: Optional[bytes])
            Processes incoming WebSocket messages and routes them to the appropriate handler
            based on the action specified in the payload.

        handle_create(data: Dict)
            Handles the creation of a new comment. Validates and serializes the
            input data before saving the comment in the database.

        handle_update(data: Dict)
            Handles updating an existing comment. Ensures the comment belongs to
            the member performing the update and validates input fields.

        handle_delete(data: Dict)
            Handles deleting an existing comment. Ensures permission and existence
            before performing the deletion.

        send_comment(event: Dict)
            Sends a serialized comment object or event message to a WebSocket client.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "comments"
        self.instance = Comment
        self.type = "send_comment"
        self.instance_serializer = CommentSerializer
        self.filter = "task_id"

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")
        action = data.get("action")
        if action == "create":
            await self.handle_create(data)
        if action == "update":
            await self.handle_update(data)
        if action == "delete":
            await self.handle_delete(data)
        if action == "get_next_batch":
            last_item_id = data["last_item_id"]
            await self.send_existing_content(self.pk, last_item_id)

    async def handle_create(self, data):
        serializer = CommentSerializer(data=data)
        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Validation errors: {serializer.errors}")
            return

        validated_data = serializer.validated_data

        content = validated_data["content"]
        task_id = validated_data["task_id"]
        headers_dict = {key.decode("utf-8"): value.decode("utf-8") for key, value in self.headers}

        auth_token = await sync_to_async(CustomAuthToken.objects.get)(key=headers_dict.get("authorization"))
        member_id = auth_token.user_id

        # Create the comment
        comment = await sync_to_async(Comment.objects.create)(
            content=content,
            member_id=member_id,
            task_id=task_id,
        )
        logger.info(f"Comment created: {comment.id}")
        # Serialize the response data
        response_serializer = CommentSerializer(comment)

        response = {
            "username": await get_username(member_id),
            "type": "send_comment",
            "comment": response_serializer.data,
            "task_id": task_id,
        }

        # Send the response to the group
        await self.channel_layer.group_send(self.group_name, response)

    async def handle_update(self, data):
        serializer = UpdateCommentSerializer(data=data)
        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            return

        validated_data = serializer.validated_data
        comment_id = validated_data["pk"]
        content = validated_data["content"]
        member_id = validated_data["member_id"]

        # Update the comment and fetch the updated instance
        rows_updated = await sync_to_async(Comment.objects.filter(id=comment_id, member_id=member_id).update)(
            content=content, updated_at=timezone.now()
        )
        if rows_updated == 0:
            error_message = {"type": "error", "message": "Comment not found or you don't have permission to update it."}
            await self.send(text_data=json.dumps(error_message))
            return

        updated_comment = await sync_to_async(Comment.objects.get)(id=comment_id)

        logger.info(f"Comment updated: {comment_id}")
        response_serializer = UpdateCommentSerializer(updated_comment)
        response = {
            "type": "send_comment",
            "comment": response_serializer.data,
        }
        await self.channel_layer.group_send(self.group_name, response)

    async def handle_delete(self, data):
        comment_id = data.get("pk")
        if not comment_id:
            error_message = {"type": "error", "message": "Comment ID is required for deletion."}
            await self.send(text_data=json.dumps(error_message))
            return

        try:
            comment = await sync_to_async(Comment.objects.get)(id=comment_id, member_id=data["member_id"])
            await sync_to_async(comment.delete)()

            response = {
                "type": "send_comment",
                "message": f"Comment {comment_id} deleted successfully.",
            }
            await self.channel_layer.group_send(self.group_name, response)

        except Comment.DoesNotExist:
            error_message = {"type": "error", "message": f"Comment with ID {comment_id} does not exist."}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Comment with ID {comment_id} does not exist.")

    async def send_comment(self, event):
        await self.send(
            text_data=json.dumps(
                event,
            )
        )


class NotificationConsumer(BaseAsyncWebsocketConsumer):
    """
    A WebSocket consumer to manage notifications for users.

    This consumer handles WebSocket communication for creating, deleting, fetching
    notifications, and sending out notification updates in real-time. It leverages Django
    channels for WebSocket handling and database synchronization for notification data.
    The class is designed to interact with Notification objects and uses serializers
    for data validation and processing.

    Attributes:
    group_name: A str representing the group to which WebSocket notifications are sent.
    instance: The Notification model class managing notification database objects.
    type: A str indicating the type key used for identifying messages.
    instance_serializer: The serializer class for validating and serializing notifications.
    filter: A str representing the key used to filter notifications for a particular user.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "notifications"
        self.instance = Notification
        self.type = "send_notification"
        self.instance_serializer = NotificationSerializer
        self.filter = "user_id"

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")
        if action == "create":
            await self.handle_create(data)
        if action == "delete":
            await self.handle_delete(data)
        if action == "get_next_batch":
            last_item_id = data["last_item_id"]
            await self.send_existing_content(self.pk, last_item_id)

    async def handle_create(self, data):
        logger.debug(f"Received data: {data}")
        serializer = NotificationSerializer(data=data)

        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Validation errors: {serializer.errors}")
            return

        validated_data = serializer.validated_data
        user_id = self.pk
        content = validated_data["content"]

        notification = await sync_to_async(Notification.objects.create)(user_id=user_id, content=content)
        logger.info(f"Notification created: {notification.id}")
        response_serializer = NotificationSerializer(notification)

        response = {
            "username": await get_username(user_id),
            "notification": response_serializer.data,
            "type": "send_notification",
        }
        await self.channel_layer.group_send(self.group_name, response)

    async def handle_delete(self, data):
        notifications_ids = data.get("notifications_ids")
        user_id = data.get("user_id")

        if not isinstance(notifications_ids, list):
            error_message = {
                "type": "error",
                "errors": {"notifications_ids": "Invalid data format. Expected a list."},
            }
            await self.send(text_data=json.dumps(error_message))
            return

        usr_notifies_ids = [
            notification_id
            for notification_id in notifications_ids
            if await sync_to_async(Notification.objects.filter(id=notification_id, user_id=user_id).exists)()
        ]

        deleted_count = await sync_to_async(
            Notification.objects.filter(id__in=usr_notifies_ids, user_id=user_id).delete
        )()

        if deleted_count[0] > 0:
            logger.info(f"{deleted_count[0]} notifications deleted for user ID: {user_id}.")
            response = {
                "type": "send_notification",
                "message": f"{deleted_count[0]} notifications deleted successfully.",
            }
            await self.channel_layer.group_send(self.group_name, response)
        else:
            error_response = {
                "type": "error",
                "message": "No notifications found to delete.",
            }
            await self.send(text_data=json.dumps(error_response))

    async def send_notification(self, event):
        try:
            recipient_emails = await get_recipients_emails(event["recipient_list"])
            print(recipient_emails)
            send_email.delay(
                subject=event["subject"],
                message=event["content"]["content"],
                to_email=recipient_emails,
            )
            await self.send(text_data=json.dumps({"message": "Notification sent successfully"}))

        except Exception as e:
            # Handle any errors gracefully
            error_message = {
                "type": "error",
                "errors": {"notification": str(e)},
            }
            await self.send(text_data=json.dumps(error_message))


class MessageConsumer(BaseAsyncWebsocketConsumer):
    """
    WebSocket consumer class to handle chat message operations including creation, update,
    deletion, and notification handling.

    The `MessageConsumer` class is designed to handle real-time messaging within chat
    applications. It processes incoming WebSocket messages, performs necessary database
    operations, and sends data to relevant channels or clients. The consumer also includes
    functionality for handling message batching, broadcasting updates, and sending
    custom notifications to chat participants or specific users.

    Attributes:
        group_name (str): Name of the WebSocket group for broadcast messaging.
        instance (Type[Message]): Reference to the model class for chat messages.
        type (str): Identifier type for WebSocket message events.
        instance_serializer (Type[MessageSerializer]): Reference to the serializer class for
            chat message objects.
        filter (str): Attribute used to filter messages based on a specific property.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "chat"
        self.instance = Message
        self.type = "send_message"
        self.instance_serializer = MessageSerializer
        self.filter = "chat_id"

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")
        action = data.get("action")
        if action == "create":
            await self.handle_create(data)
        elif action == "update":
            await self.handle_update(data)
        elif action == "delete":
            await self.handle_delete(data)
        if action == "get_next_batch":
            last_item_id = data["last_item_id"]
            await self.send_existing_content(self.pk, last_item_id)

    async def handle_create(self, data):
        serializer = MessageSerializer(data=data)

        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Validation errors: {serializer.errors}")
            return

        validated_data = serializer.validated_data
        headers_dict = {key.decode("utf-8"): value.decode("utf-8") for key, value in self.headers}
        chat_id = validated_data["chat_id"]
        auth_token = await sync_to_async(CustomAuthToken.objects.get)(key=headers_dict.get("authorization"))
        sender_id = auth_token.user_id
        content = validated_data["content"]
        chat_participants = await sync_to_async(
            lambda: list(Participant.objects.filter(chat_id=chat_id).values_list("user_id", flat=True))
        )()
        if sender_id not in chat_participants:
            error_message = {
                "type": "error",
                "errors": {"chat_participants": "sender_id not in chat_participants"},
            }
            return await self.send(text_data=json.dumps(error_message))
        # Create message
        message = await sync_to_async(Message.objects.create)(chat_id=chat_id, sender_id=sender_id, content=content)
        logger.info(f"Message created: {message.id}")

        # Prepare response for the message sender
        response_serializer = MessageSerializer(message)
        username = await get_username(sender_id)
        response = {
            "username": username,
            "type": "send_message",
            "chat_id": chat_id,
            "message": response_serializer.data,
        }
        chat_participants.remove(sender_id)
        recipient_ids = chat_participants
        # Increment message count for sender
        msg_counter = await sync_to_async(Message.objects.filter(chat_id=chat_id, sender_id=sender_id).count)()
        chat_name = await sync_to_async(Chat.objects.get)(id=chat_id)
        # Send notification to the `notifications_room`
        notify_content = {
            "content": f"You've received {msg_counter} messages in chat: {chat_name}!",
        }

        for recipient_id in recipient_ids:
            notification_event = {
                "type": "send_notification",
                "subject": f"You've received new message in chat: {chat_name}",
                "recipient_list": recipient_ids,
                "user_id": recipient_id,
                "content": notify_content,
            }
            await sync_to_async(Notification.objects.create)(user_id=recipient_id, content=notify_content)
            await self.channel_layer.group_send("notifications_room", notification_event)

        # Send message to `messages_room`
        await self.channel_layer.group_send(self.group_name, response)

    async def handle_update(self, data):
        serializer = UpdateMessageSerializer(data=data)
        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            return
        validated_data = serializer.validated_data
        msg_id = validated_data["pk"]
        chat_id = validated_data["chat_id"]
        sender_id = validated_data["sender_id"]
        content = validated_data["content"]

        rows_updated_msg = await sync_to_async(
            Message.objects.filter(id=msg_id, chat_id=chat_id, sender_id=sender_id).update
        )(content=content, updated_at=timezone.now())
        if rows_updated_msg == 0:
            error_message = {"type": "error", "message": "Message not found or you don't have permission to update it."}
            await self.send(text_data=json.dumps(error_message))
            return
        updated_msg = await sync_to_async(Message.objects.get)(id=msg_id)
        logger.info(f"Message updated: {msg_id}")
        response_serializer = MessageSerializer(updated_msg)
        response = {
            "type": "send_message",
            "content": response_serializer.data,
        }
        await self.channel_layer.group_send(self.group_name, response)

    async def handle_delete(self, data):
        msg_id = data["pk"]
        if not msg_id:
            error_message = {"type": "error", "message": "Message not found."}
            await self.send(text_data=json.dumps(error_message))
            return
        try:
            msg = await sync_to_async(Message.objects.get)(id=msg_id, sender_id=data["sender_id"])
            await sync_to_async(msg.delete)()

            response = {"type": "send_message", "message": f"Message {msg_id} has been successfully deleted."}
            await self.channel_layer.group_send(self.group_name, response)
        except Message.DoesNotExist:
            error_message = {"type": "error", "message": "Message not found."}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Message with id {msg_id} does not exist")
            return

    async def send_message(self, event):

        await self.send(
            text_data=json.dumps(
                event,
            )
        )
