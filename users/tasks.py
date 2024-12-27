from celery import shared_task
from django.core.mail import send_mail
from django.core.management import call_command

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


@shared_task
def cleanup_expired_tokens():
    """
    Task to remove expired tokens via Django command.
    """
    call_command("cleanup_expired_tokens")
