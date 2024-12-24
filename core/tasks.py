from core.settings import DEFAULT_FROM_EMAIL
from celery import shared_task
from django.core.mail.message import EmailMultiAlternatives


@shared_task
def send_email(subject, message, to_email, **kwargs):
    print("send_email task called")
    try:
        msg = EmailMultiAlternatives(subject, message, DEFAULT_FROM_EMAIL, to_email)
        msg.content_subtype = "html"
        msg.send()
    except Exception as e:
        print(f"Error sending email: {e}")
