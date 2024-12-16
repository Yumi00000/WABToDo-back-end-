import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from users.models import CustomUser
from websocket.models import Comment, Notification
from websocket.serializers import CommentSerializer, NotificationSerializer

logger = logging.getLogger(__name__)


class CommentConsumer(AsyncWebsocketConsumer):
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

        username = validated_data["username"]
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
            "username": username,
            "type": "send_comment",
            "comment": response_serializer.data,
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

        @sync_to_async
        def get_username(user_pk):
            db_response = CustomUser.objects.get(id=user_pk).username
            return db_response

        username = await get_username(user_id)
        response = {
            "username": username,
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
