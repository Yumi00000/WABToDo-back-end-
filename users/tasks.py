from celery import shared_task
from django.core.mail import send_mail

from core import settings


@shared_task
def send_email(email: str, signed_url: str) -> None:
    send_mail(
        "Registration complete",
        "Click here to activate your account: " + signed_url,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )
