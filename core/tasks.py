import json

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.apps import apps
from django.core.mail.message import EmailMultiAlternatives

from core.settings import DEFAULT_FROM_EMAIL
from websocket.serializers import get_serializer


@shared_task
def send_email(subject, message, to_email, **kwargs):
    print("send_email task called")
    try:
        msg = EmailMultiAlternatives(subject, message, DEFAULT_FROM_EMAIL, to_email)
        msg.content_subtype = "html"
        msg.send()
    except Exception as e:
        print(f"Error sending email: {e}")


@shared_task
def send_chunked_data(group_name, instance_model, instance_serializer_class, filter_kwargs, batch_size):
    models = apps.get_app_config("websocket")

    model = models.get_model(instance_model)

    serializer = get_serializer(instance_serializer_class)
    queryset = model.objects.filter(**filter_kwargs).order_by("-created_at")[:batch_size]
    serialized_data = serializer(queryset, many=True)

    response = {
        "type": "send_data_chunk",  # Event type handled by WebSocket
        "data": serialized_data.data,
    }

    # Send data to the WebSocket group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "send_data_chunk", "message": json.dumps(response)},
    )
