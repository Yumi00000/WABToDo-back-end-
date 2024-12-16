import os

from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path

from websocket import consumers
from websocket.middlewares import WebSocketJWTAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": WebSocketJWTAuthMiddleware(
            URLRouter(
                [
                    re_path(r"^ws/comnt/$", consumers.CommentConsumer.as_asgi()),
                    re_path(r"^ws/notify/$", consumers.NotificationConsumer.as_asgi()),
                    re_path(r"^ws/msg/$", consumers.MessageConsumer.as_asgi()),
                ]
            )
        ),
    }
)

channel_layer = get_channel_layer()
