import json
import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.apps import apps
from django.core.mail.message import EmailMultiAlternatives

from core.settings import DEFAULT_FROM_EMAIL
from websocket.serializers import get_serializer

logger = logging.getLogger(__name__)


@shared_task
def send_email(subject, message, to_email, **kwargs):
    """
    Task function to send an email using Django's EmailMultiAlternatives.

    This function serves as a Celery shared task to handle the sending of emails
    asynchronously. It uses the EmailMultiAlternatives class to send messages
    with the capability to support both plain-text and HTML content. In case of
    an exception during the email sending process, the error is printed to the
    console for debugging.

    Args:
        subject (str): The subject of the email.
        message (str): The message content of the email.
        to_email (list[str]): A list of recipient email addresses.
        **kwargs: Additional keyword arguments.

    Raises:
        Exception: Any error that occurs during the process of sending an email.
    """
    print("send_email task called")
    try:
        msg = EmailMultiAlternatives(subject, message, DEFAULT_FROM_EMAIL, to_email)
        msg.content_subtype = "html"
        msg.send()
    except Exception as e:
        print(f"Error sending email: {e}")


@shared_task
def send_chunked_data(group_name, instance_model, instance_serializer_class, filter_kwargs, batch_size):
    """
        Sends chunked data to a specified WebSocket group by querying model instances,
        serializing them, and routing the serialized data through a channel layer. This task
        is designed to facilitate efficient data transmission in chunks via WebSockets.

        Args:
            group_name (str): The name of the WebSocket group to which data should
                be sent.
            instance_model (str): The name of the model class to be queried for
                fetching data.
            instance_serializer_class (str): The fully qualified name of the
                serializer class used to serialize the model instances.
            filter_kwargs (dict): A dictionary of filter conditions to query the
                desired model instances.
            batch_size (int): The maximum number of model instances to fetch from
                the database.

        Returns:
            None
    """
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


@shared_task
def on_delete_time_item(instance_model, instance_pk, app_label):
    """
    This function orchestrates the deletion of an instance of a specified model via its primary key. It retrieves
    the model associated with the given app label and dynamically removes the identified instance. Logging is
    performed for both successful deletions and any errors encountered during the operation.

    Args:
        instance_model (str): The name of the model whose instance is to be deleted.
        instance_pk (int): The primary key of the model instance to delete.
        app_label (str): The label of the app containing the target model.

    Raises:
        Exception: An exception is raised, logged, and handled internally if there is an error in fetching or
        deleting the instance of the specified model.
    """
    logger.debug("on_delete_time_item called")
    try:
        models = apps.get_app_config(app_label)
        model = models.get_model(instance_model)
        instance = model.objects.get(id=instance_pk)
        instance.delete()
        logger.info(f"Successfully deleted {instance_model} with ID {instance_pk}.")
    except Exception as e:
        logger.error(f"Error deleting {instance_model} with ID {instance_pk}: {e}")
