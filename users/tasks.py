from celery import shared_task
from django.core.mail import send_mail
from django.core.management import call_command

from core import settings


@shared_task
def send_email(email: str, signed_url: str) -> None:
    """
    This function is a Celery shared task that facilitates sending an email with a registration link.
    It constructs and sends an email with a predefined subject and body format, which includes
    a signed URL to activate the user's account.

    Arguments:
        email: A string containing the recipient's email address.
        signed_url: A string representing the activation URL included in the email body.

    Returns:
        None
    """
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
    Performs cleanup of expired tokens using the Django management command "cleanup_expired_tokens".

    Summary:
    This function, designed as a Celery shared task, executes the
    "cleanup_expired_tokens" Django management command to delete expired tokens
    from the database. It is intended to automate token maintenance tasks
    through periodic scheduling within a Celery-enabled environment.

    Raises:
    None

    Parameters:
    None

    Returns:
    None
    """
    call_command("cleanup_expired_tokens")
