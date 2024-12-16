import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from users.models import CustomUser, Participant
from websocket.models import Comment, Notification, Message
from websocket.serializers import CommentSerializer, NotificationSerializer, MessageSerializer

logger = logging.getLogger(__name__)


@sync_to_async
def get_username(user_pk):
    db_response = CustomUser.objects.get(id=user_pk).username
    return db_response


@sync_to_async
def get_chat_participants(chat_id, sender_id):
    participants = Participant.objects.filter(chat_id=chat_id).exclude(user_id=sender_id)
    return list(participants)


class SendCommentConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "comments_room"

    async def connect(self):
        logger.info("WebSocket connected")
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")

        # Validate the incoming data using the serializer
        serializer = CommentSerializer(data=data)
        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Validation errors: {serializer.errors}")
            return

        validated_data = serializer.validated_data

        member_id = validated_data["member_id"]
        content = validated_data["content"]
        task_id = validated_data["task_id"]

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

    async def send_comment(self, event):
        await self.send(
            text_data=json.dumps(
                event,
            )
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "notifications_room"

    async def connect(self):
        logger.info("WebSocket connected")
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")
        serializer = NotificationSerializer(data=data)

        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Validation errors: {serializer.errors}")
            return

        validated_data = serializer.validated_data
        user_id = validated_data["user_id"]
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

    async def send_notification(self, event):
        await self.send(
            text_data=json.dumps(
                event,
            )
        )


class SendMessageConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "messages_room"

    async def connect(self):
        logger.info("WebSocket connected")
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")
        serializer = MessageSerializer(data=data)

        if not serializer.is_valid():
            error_message = {"type": "error", "errors": serializer.errors}
            await self.send(text_data=json.dumps(error_message))
            logger.error(f"Validation errors: {serializer.errors}")
            return

        validated_data = serializer.validated_data

        chat_id = validated_data["chat_id"]
        sender_id = validated_data["sender_id"]
        content = validated_data["content"]

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

        chat_participants = await get_chat_participants(chat_id, sender_id)
        recipient_ids = [participant.user_id for participant in chat_participants]

        # Increment message count for sender
        msg_counter = await sync_to_async(Message.objects.filter(chat_id=chat_id, sender_id=sender_id).count)()

        # Send notification to the `notifications_room`
        notify_content = {
            "content": f"You've received {msg_counter} messages!",
        }
        for recipient_id in recipient_ids:
            notification_event = {
                "type": "send_notification",
                "user_id": recipient_id,
                "content": notify_content,
            }
            await sync_to_async(Notification.objects.create)(user_id=recipient_id, content=notify_content)
            await self.channel_layer.group_send("notifications_room", notification_event)

        # Send message to `messages_room`
        await self.channel_layer.group_send(self.group_name, response)

    async def send_message(self, event):
        await self.send(
            text_data=json.dumps(
                event,
            )
        )
