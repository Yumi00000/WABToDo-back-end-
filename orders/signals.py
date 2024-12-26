import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .serializers import UpdateOrderSerializer

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def handle_schedule_delete(sender, instance, **kwargs):
    logger.info(f"Signal triggered for Order ID: {instance.id}")
    if instance.on_delete_date:
        logger.info(f"Scheduling delete task for Order ID: {instance.id}")
        serializer = UpdateOrderSerializer()
        serializer.schedule_delete(instance)